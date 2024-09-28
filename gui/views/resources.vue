<template lang="pug">
div
  div
    h1.has-text-weight-bold Resources
    p Import - Export Adversaries
  hr
  div
    .columns
      .column.is-4.buttons.m-0.is-flex.is-justify-content-flex-start
        button.button.is-primary.is-small.level-item(@click="showExportModal = true")
          span.icon
            i.fas.fa-plus
          span Export
        button.button.is-info.is-small.level-item(@click="showImportModal = true")
          span.icon
            i.fas.fa-file-import
          span Import

  // Export Modal
  div.modal(:class="{ 'is-active': showExportModal }")
    div.modal-background(@click="closeExportModal")
    div.modal-card
      header.modal-card-head
        p.modal-card-title Export Adversary
        button.delete(@click="closeExportModal", aria-label="close")
      section.modal-card-body
        div(v-if="loading" class="has-text-centered")
          button.button.is-loading.is-large.is-light.disabled Loading...
        div(v-else)
          form#standAloneForm
            .field
              label.label Adversary
              .control
                .select.is-fullwidth(:class="{ 'is-danger': !selectedAdversary && showErrors }")
                  select(name="adversary" v-model="selectedAdversary")
                    option(value="" disabled) Select an adversary
                    option(v-for="adversary in adversaries" :key="adversary.adversary_id" :value="adversary.adversary_id")
                      | {{ adversary.name }}
                p.help.is-danger(v-if="!selectedAdversary && showErrors") Adversary is required

      footer.modal-card-foot
        button.button.is-success(@click="submitExportForm") Save
        button.button(@click="closeExportModal") Cancel

  // Import Modal
  div.modal(:class="{ 'is-active': showImportModal }")
    div.modal-background(@click="closeImportModal")
    div.modal-card
      header.modal-card-head
        p.modal-card-title Import Adversary
        button.delete(@click="closeImportModal", aria-label="close")
      section.modal-card-body
        p.block Import an adversary in JSON format. Export any existing adversary to see the required format.
        .file.has-name.is-fullwidth
          label.file-label
            input.file-input(type="file", accept=".json" @change="handleFileUpload")
            span.file-cta
              span.file-icon
                font-awesome-icon(icon="fas fa-upload")
              span.file-label Choose a file...
            span.file-name {{ fileName ? fileName : 'No file chosen' }}
        p.help.is-danger(v-if="showErrors && !fileContent") File is required
        p.help.is-danger(v-if="fileError") {{ fileError }}

      footer.modal-card-foot
        button.button.is-success(@click="submitImportForm") Upload
        button.button(@click="closeImportModal") Cancel
</template>

<script>
export default {
  inject: ["$api"],
  data() {
    return {
      showExportModal: false,
      showImportModal: false,
      showErrors: false, // Control for error messages
      loading: false, // Control for loading state
      adversaries: [], // Will hold the fetched adversaries
      selectedAdversary: "", // Selected adversary for export
      fileContent: null, // Content of the uploaded JSON file
      fileName: "", // Name of the uploaded file
      fileError: "", // Error message for file validation
    };
  },
  computed: {
    selectedAdversaryName() {
      const adversary = this.adversaries.find(a => a.adversary_id === this.selectedAdversary);
      return adversary ? adversary.name : '';
    }
  },
  methods: {
    loadAdversaries() {
      this.loading = true;
      this.$api.get('/plugin/resources/get_adversaries')
        .then(response => {
          const adversaryData = response.data;
          if (adversaryData && adversaryData.adversaries) {
            this.adversaries = adversaryData.adversaries;
          } else {
            console.warn('Unexpected data format for adversaries:', adversaryData);
          }
        })
        .catch(error => {
          console.error('Error loading adversaries:', error);
          alert('Failed to load adversaries. Please try again later.');
        })
        .finally(() => {
          this.loading = false;
        });
    },
    handleFileUpload(event) {
      const file = event.target.files[0];
      this.fileError = ""; // Reset file error message
      this.fileContent = null; // Reset file content
      if (file) {
        if (!file.name.endsWith('.json')) {
          this.fileError = "Please upload a valid JSON file.";
          return;
        }
        this.fileName = file.name;
        const reader = new FileReader();
        reader.onload = (e) => {
          try {
            const jsonData = JSON.parse(e.target.result);

            this.fileContent = jsonData;
          } catch (error) {
            this.fileError = 'Invalid JSON file content or structure.';
            this.fileContent = null;
          }
        };
        reader.readAsText(file);
      }
    },
    submitExportForm() {
      // Validate all fields
      this.showErrors = true;
      if (!this.selectedAdversary) {
        console.log('Validation failed, please fill all the required fields.');
        return;
      }

      const adversaryName = this.selectedAdversaryName || 'adversary';

      this.loading = true;

      this.$api.get(`/plugin/resources/export/${this.selectedAdversary}`, { responseType: 'blob' })
        .then(response => {
          console.log('Form submitted successfully:', response);

          // Create a new blob object from the response data
          const blob = new Blob([response.data], { type: 'application/json' });

          // Create a link element
          const link = document.createElement('a');
          link.href = window.URL.createObjectURL(blob);

          // Set the download attribute with a filename based on the adversary name
          link.download = `${adversaryName}.json`;

          // Append link to the body
          document.body.appendChild(link);

          // Programmatically click the link to trigger the download
          link.click();

          // Remove the link after download
          document.body.removeChild(link);

          this.closeExportModal();
        })
        .catch(error => {
          console.error('Error submitting form:', error);
          alert('Failed to export adversary. Please try again later.');
        })
        .finally(() => {
          this.loading = false;
        });
    },
    submitImportForm() {
      this.showErrors = true;
      if (!this.fileContent) {
        console.log('Validation failed, no file uploaded.');
        return;
      }

      console.log('Validation passed, uploading file content...', this.fileContent);

      // Set loading state to true before sending request
      this.loading = true;

      // Send POST request with the file content
      this.$api.post('/plugin/resources/import', this.fileContent)
        .then(response => {
          console.log('File uploaded successfully:', response);
          alert('File imported successfully.');
          this.closeImportModal();
        })
        .catch(error => {
          console.error('Error uploading file:', error);
          alert('Failed to import file. Please try again later.');
        })
        .finally(() => {
          this.loading = false;
        });
    },
    closeExportModal() {
      this.showExportModal = false;
      this.showErrors = false;
      this.selectedAdversary = '';
    },
    closeImportModal() {
      this.showImportModal = false;
      this.showErrors = false;
      this.fileContent = null;
      this.fileName = '';
      this.fileError = '';
    }
  },
  mounted() {
    this.loadAdversaries();
  }
};
</script>

<style scoped>

.modal.is-active {
  display: flex;
}
.executor-checkbox {
  margin-right: 15px;
}
.is-danger {
  border-color: red;
}
</style>
