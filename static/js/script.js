// Wait for the DOM to be fully loaded
document.addEventListener('DOMContentLoaded', function() {
    // Auto-dismiss flash messages after 5 seconds
    const flashMessages = document.querySelectorAll('.flash-message');
    
    if (flashMessages.length > 0) {
        setTimeout(function() {
            flashMessages.forEach(function(message) {
                message.style.opacity = '0';
                setTimeout(function() {
                    message.style.display = 'none';
                }, 300);
            });
        }, 5000);
    }
    
    // File input styling - show the selected file name
    const fileInput = document.getElementById('file');
    
    if (fileInput) {
        fileInput.addEventListener('change', function() {
            const fileName = this.files[0] ? this.files[0].name : 'No file chosen';
            const fileNameDisplay = document.createElement('span');
            fileNameDisplay.textContent = fileName;
            fileNameDisplay.className = 'file-name';
            
            // Remove any previous file name display
            const prevDisplay = this.parentElement.querySelector('.file-name');
            if (prevDisplay) {
                prevDisplay.remove();
            }
            
            this.parentElement.appendChild(fileNameDisplay);
        });
    }
});
