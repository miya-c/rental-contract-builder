document.addEventListener('DOMContentLoaded', function() {
    // Auto dismiss alerts after 5 seconds
    setTimeout(function() {
        const alerts = document.querySelectorAll('.alert-dismissible:not(.alert-danger)');
        alerts.forEach(function(alert) {
            const bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        });
    }, 5000);

    // Initialize tooltips
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    // Handle building form custom fields
    const structureField = document.getElementById('structure');
    const customStructureContainer = document.getElementById('custom-structure-container');
    
    if (structureField && customStructureContainer) {
        structureField.addEventListener('change', function() {
            if (this.value === 'その他') {
                customStructureContainer.style.display = 'block';
            } else {
                customStructureContainer.style.display = 'none';
            }
        });
        
        // Trigger on page load
        if (structureField.value === 'その他') {
            customStructureContainer.style.display = 'block';
        }
    }

    const roofStructureField = document.getElementById('roof_structure');
    const customRoofStructureContainer = document.getElementById('custom-roof-structure-container');
    
    if (roofStructureField && customRoofStructureContainer) {
        roofStructureField.addEventListener('change', function() {
            if (this.value === 'その他') {
                customRoofStructureContainer.style.display = 'block';
            } else {
                customRoofStructureContainer.style.display = 'none';
            }
        });
        
        // Trigger on page load
        if (roofStructureField.value === 'その他') {
            customRoofStructureContainer.style.display = 'block';
        }
    }

    const buildingTypeField = document.getElementById('building_type');
    const customBuildingTypeContainer = document.getElementById('custom-building-type-container');
    
    if (buildingTypeField && customBuildingTypeContainer) {
        buildingTypeField.addEventListener('change', function() {
            if (this.value === 'その他') {
                customBuildingTypeContainer.style.display = 'block';
            } else {
                customBuildingTypeContainer.style.display = 'none';
            }
        });
        
        // Trigger on page load
        if (buildingTypeField.value === 'その他') {
            customBuildingTypeContainer.style.display = 'block';
        }
    }

    // Handle contract creation form - dynamic data loading
    const roomSelect = document.getElementById('room_id');
    const agentSelect = document.getElementById('agent_id');
    
    if (roomSelect) {
        roomSelect.addEventListener('change', function() {
            const roomId = this.value;
            if (roomId) {
                fetch(`/api/room-details/${roomId}`)
                    .then(response => response.json())
                    .then(data => {
                        // Populate building and owner info in the form
                        document.getElementById('building-info').innerHTML = `
                            <p><strong>建物名:</strong> ${data.building.name}</p>
                            <p><strong>住所:</strong> ${data.building.address}</p>
                            <p><strong>構造:</strong> ${data.building.structure}</p>
                            <p><strong>建物タイプ:</strong> ${data.building.building_type}</p>
                        `;
                        
                        document.getElementById('room-info').innerHTML = `
                            <p><strong>部屋番号:</strong> ${data.room_number}</p>
                            <p><strong>間取り:</strong> ${data.layout}</p>
                            <p><strong>床面積:</strong> ${data.floor_area} m²</p>
                            <p><strong>階:</strong> ${data.floor}</p>
                        `;
                        
                        document.getElementById('owner-info').innerHTML = `
                            <p><strong>オーナー名:</strong> ${data.owner.name}</p>
                            <p><strong>住所:</strong> ${data.owner.address}</p>
                        `;
                        
                        // Show the info sections
                        document.getElementById('property-details-container').style.display = 'block';
                    })
                    .catch(error => {
                        console.error('Error fetching room details:', error);
                    });
            } else {
                document.getElementById('property-details-container').style.display = 'none';
            }
        });
    }
    
    if (agentSelect) {
        agentSelect.addEventListener('change', function() {
            const agentId = this.value;
            if (agentId) {
                fetch(`/api/agent-details/${agentId}`)
                    .then(response => response.json())
                    .then(data => {
                        // Populate agent info
                        document.getElementById('agent-info').innerHTML = `
                            <p><strong>宅建士名:</strong> ${data.name}</p>
                            <p><strong>免許番号:</strong> ${data.license_number}</p>
                        `;
                        
                        // Show the info section
                        document.getElementById('agent-info-container').style.display = 'block';
                    })
                    .catch(error => {
                        console.error('Error fetching agent details:', error);
                    });
            } else {
                document.getElementById('agent-info-container').style.display = 'none';
            }
        });
    }

    // Special term selection preview
    const specialTermCheckboxes = document.querySelectorAll('input[name="special_terms"]');
    if (specialTermCheckboxes.length > 0) {
        specialTermCheckboxes.forEach(checkbox => {
            checkbox.addEventListener('change', function() {
                updateSpecialTermsPreview();
            });
        });
        
        // Initial update
        updateSpecialTermsPreview();
    }

    function updateSpecialTermsPreview() {
        const previewContainer = document.getElementById('special-terms-preview');
        if (!previewContainer) return;
        
        let selectedTerms = [];
        document.querySelectorAll('input[name="special_terms"]:checked').forEach(checkbox => {
            const termId = checkbox.value;
            
            fetch(`/api/special-term-details/${termId}`)
                .then(response => response.json())
                .then(data => {
                    const termDiv = document.createElement('div');
                    termDiv.className = 'mb-3 p-2 border-bottom';
                    termDiv.innerHTML = `<h6>${data.title}</h6><p>${data.content}</p>`;
                    
                    selectedTerms.push(termDiv);
                    
                    // Clear and rebuild the preview
                    previewContainer.innerHTML = '';
                    if (selectedTerms.length > 0) {
                        selectedTerms.forEach(term => {
                            previewContainer.appendChild(term);
                        });
                        document.getElementById('special-terms-preview-container').style.display = 'block';
                    } else {
                        document.getElementById('special-terms-preview-container').style.display = 'none';
                    }
                })
                .catch(error => {
                    console.error('Error fetching term details:', error);
                });
        });
        
        // If no terms selected, hide the preview
        if (document.querySelectorAll('input[name="special_terms"]:checked').length === 0) {
            document.getElementById('special-terms-preview-container').style.display = 'none';
        }
    }

    // Contract template preview functionality
    const previewTemplateButton = document.getElementById('preview-template');
    if (previewTemplateButton) {
        previewTemplateButton.addEventListener('click', function(e) {
            e.preventDefault();
            
            const templateContent = document.getElementById('file_content').value;
            if (templateContent) {
                const previewWindow = window.open('', '_blank');
                previewWindow.document.write(templateContent);
                previewWindow.document.close();
            } else {
                alert('テンプレート内容を入力してください。');
            }
        });
    }

    // Delete confirmation functionality
    const deleteButtons = document.querySelectorAll('.delete-confirm');
    deleteButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            if (!confirm('本当に削除しますか？この操作は元に戻せません。')) {
                e.preventDefault();
            }
        });
    });
});
