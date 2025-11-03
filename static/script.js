document.addEventListener('DOMContentLoaded', () => {

    // --- 1. SNIPPET EXPAND/COLLAPSE ---
    // Find all snippet code blocks
    const snippetWrappers = document.querySelectorAll('.snippet-code-wrapper');
    
    snippetWrappers.forEach(wrapper => {
        // Add a click event listener to the wrapper div
        wrapper.addEventListener('click', () => {
            const codeBlock = wrapper.querySelector('.snippet-code');
            codeBlock.classList.toggle('expanded');
        });
    });

    // --- 2. COPY CODE BUTTON ---
    const copyButtons = document.querySelectorAll('.copy-btn');
    
    copyButtons.forEach(button => {
        button.addEventListener('click', (event) => {
            // Stop the click from also triggering the 'expand' function
            event.stopPropagation(); 
            
            // Find the code block within the same snippet-card
            const card = button.closest('.snippet-card');
            const code = card.querySelector('.snippet-code code').innerText;

            // Use the modern clipboard API
            navigator.clipboard.writeText(code).then(() => {
                // Give user feedback
                button.innerText = 'Copied!';
                setTimeout(() => {
                    button.innerText = 'Copy Code';
                }, 2000);
            }).catch(err => {
                console.error('Failed to copy text: ', err);
            });
        });
    });

    // --- 3. SAVE SNIPPET BUTTON ---
    const saveButtons = document.querySelectorAll('.save-btn');
    
    saveButtons.forEach(button => {
        button.addEventListener('click', (event) => {
            event.stopPropagation(); // Stop expand/collapse
            
            const snippetId = button.dataset.snippetId;
            
            // Send a request to our Flask backend
            fetch(`/save_snippet/${snippetId}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                }
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    // Update the button text based on the action
                    if (data.action === 'saved') {
                        button.innerText = 'Unsave';
                        button.classList.remove('btn-red');
                        button.classList.add('btn-yellow');
                    } else { // 'unsaved'
                        // If we are on the dashboard, removing it should just hide the card
                        if (window.location.pathname.includes('/dashboard')) {
                            button.closest('.snippet-card').style.display = 'none';
                        } else {
                            button.innerText = 'Save';
                            button.classList.remove('btn-yellow');
                            button.classList.add('btn-red'); // Or whatever the 'save' color is
                        }
                    }
                } else {
                    alert('Error saving snippet: ' + data.error);
                }
            })
            .catch(err => console.error('Fetch error:', err));
        });
    });
});