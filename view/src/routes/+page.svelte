<script>
    let file;
  
    async function handleUpload() {
      if (!file) return;
  
      const formData = new FormData();
      formData.append('file', file);
  
      const response = await fetch('http://localhost:8000/upload', {
        method: 'POST',
        body: formData,
      });
  
      if (response.ok) {
        // Redirect to the results page
        window.location.href = '/results';
      } else {
        alert('Upload failed');
      }
    }
  </script>
  
  <div class="upload-container">
    <input type="file" accept=".mp4,.mov" bind:files={file} />
    <button on:click={handleUpload}>Upload</button>
  </div>
  
  <style>
    .upload-container {
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      height: 100vh;
      background-color: #f0f0f0;
      font-family: Arial, sans-serif;
    }
  
    input[type="file"] {
      margin: 20px 0;
      padding: 10px;
      font-size: 16px;
    }
  
    button {
      padding: 10px 20px;
      font-size: 16px;
      background-color: #007BFF;
      color: white;
      border: none;
      border-radius: 5px;
      cursor: pointer;
    }
  
    button:hover {
      background-color: #0056b3;
    }
  </style>
  