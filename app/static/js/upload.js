function uploadFile(formData) {
    const progressBar = document.getElementById('upload-progress');
    const statusText = document.getElementById('upload-status');
    let uploadId = null;

    // Show progress bar
    progressBar.style.display = 'block';
    progressBar.value = 0;

    fetch('/data/upload', {
        method: 'POST',
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        if (data.error) {
            throw new Error(data.error);
        }
        uploadId = data.upload_id;
        checkProgress(uploadId);
    })
    .catch(error => {
        statusText.textContent = `Error: ${error.message}`;
        progressBar.style.display = 'none';
    });
}

function checkProgress(uploadId) {
    const progressBar = document.getElementById('upload-progress');
    const statusText = document.getElementById('upload-status');
    
    const checkStatus = setInterval(() => {
        fetch(`/data/upload/progress/${uploadId}`)
            .then(response => response.json())
            .then(data => {
                progressBar.value = data.progress;
                
                if (data.status === 'completed') {
                    statusText.textContent = 'Upload completed!';
                    clearInterval(checkStatus);
                } else if (data.status === 'error') {
                    statusText.textContent = `Error: ${data.error}`;
                    clearInterval(checkStatus);
                } else {
                    statusText.textContent = `Uploading: ${Math.round(data.progress)}%`;
                }
            })
            .catch(error => {
                statusText.textContent = `Error checking progress: ${error.message}`;
                clearInterval(checkStatus);
            });
    }, 1000);
}