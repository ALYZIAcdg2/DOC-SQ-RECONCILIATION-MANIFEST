/**
 * SIA LOGIC CENTRALISÉE
 * Gère : Majuscules, Auto-save, Brouillons, Chargement et Envoi PDF
 */

// --- CONFIGURATION ET ÉLÉMENTS ---
const selectVol = document.getElementById('flight-select');
const volDisplay = document.getElementById('vol-display');
const dateInput = document.getElementById('date-input') || document.getElementById('dateMain');
const formToPrint = document.getElementById('form-to-print') || document.getElementById('pdf');
const formTitle = document.title || "DOCUMENT_SIA";

// --- 1. GESTION DES MAJUSCULES AUTOMATIQUES ---
document.addEventListener('input', (e) => {
    // Transforme en majuscules sauf pour les champs de type date
    if ((e.target.tagName === 'INPUT' && e.target.type !== 'date') || e.target.tagName === 'TEXTAREA') {
        e.target.value = e.target.value.toUpperCase();
    }
});

// --- 2. MISE À JOUR DU VOL (DANS LE BANDEAU GRIS) ---
if (selectVol && volDisplay) {
    selectVol.addEventListener('change', (e) => { 
        volDisplay.textContent = e.target.value; 
    });
}

// --- 3. SAUVEGARDE AUTOMATIQUE (BUFFER) ---
function autoSave() {
    const formData = {};
    document.querySelectorAll('input, select, textarea').forEach(el => {
        if (el.id) {
            formData[el.id] = (el.type === 'checkbox' || el.type === 'radio') ? el.checked : el.value;
        }
    });
    localStorage.setItem(window.location.pathname, JSON.stringify(formData));
}

// --- 4. CHARGEMENT DES DONNÉES ---
function loadSavedData() {
    const resumeData = localStorage.getItem("RESUME_DATA");
    const autoSavedData = localStorage.getItem(window.location.pathname);
    const data = resumeData ? JSON.parse(resumeData) : (autoSavedData ? JSON.parse(autoSavedData) : null);
    
    if (data) {
        Object.keys(data).forEach(id => {
            const el = document.getElementById(id);
            if (el) {
                if (el.type === 'checkbox' || el.type === 'radio') el.checked = data[id];
                else el.value = data[id];
            }
        });
        // Nettoyage si c'est une reprise de brouillon depuis l'accueil
        if (resumeData) localStorage.removeItem("RESUME_DATA");
        // Update visuel du vol
        if (selectVol && volDisplay) volDisplay.textContent = selectVol.value;
    }
}

// --- 5. SAUVEGARDE D'UN BROUILLON OFFICIEL ---
function saveDraft() {
    const flight = selectVol ? selectVol.value : "REF";
    const date = dateInput ? dateInput.value : "SANS-DATE";
    const draftID = `DRAFT_${formTitle.replace(/\s+/g, '_')}_${flight}_${date}`;

    if (localStorage.getItem(draftID)) {
        if (!confirm(`Un brouillon existe déjà.\nÉcraser la sauvegarde actuelle ?`)) return;
    }
    
    const formData = {};
    document.querySelectorAll('input, select, textarea').forEach(el => { if(el.id) formData[el.id] = el.value; });
    
    localStorage.setItem(draftID, JSON.stringify({ 
        type: formTitle, 
        url: window.location.pathname, 
        date: new Date().toLocaleString(), 
        data: formData 
    }));
    alert("Brouillon sauvegardé !");
}

// --- 6. ENVOI DU DOCUMENT (GENERATION PDF + SERVEUR) ---
async function saveAndSend() {
    if (!formToPrint) {
        alert("Erreur: Conteneur d'impression non trouvé.");
        return;
    }

    const flight = selectVol ? selectVol.value : "SIA";
    const dateStr = dateInput ? dateInput.value : "SANS-DATE";
    const fileName = `${formTitle.replace(/\s+/g, '_')}_${flight}_${dateStr}.pdf`;

    const opt = { 
        margin: 0, 
        filename: fileName, 
        image: { type: 'jpeg', quality: 0.98 }, 
        html2canvas: { scale: 2, useCORS: true }, 
        jsPDF: { unit: 'mm', format: 'a4', orientation: 'landscape' } 
    };

    // Note: On vérifie si portrait est nécessaire (pour certains formulaires comme UM Waiver)
    if (window.innerHeight > window.innerWidth) {
        opt.jsPDF.orientation = 'portrait';
    }

    try {
        // 1. Sauvegarde locale pour l'utilisateur
        html2pdf().set(opt).from(formToPrint).save();
        
        // 2. Génération du Blob pour le serveur
        const pdfBlob = await html2pdf().set(opt).from(formToPrint).output('blob');
        const formData = new FormData();
        formData.append('pdf', pdfBlob, fileName);
        formData.append('filename', fileName);
        formData.append('subject', `${formTitle} - ${flight} - ${dateStr}`);
        formData.append('body', `Veuillez trouver ci-joint le document ${formTitle}.`);

        // 3. Envoi au serveur
        const response = await fetch("/send-pdf", { method: 'POST', body: formData });
        
        if (response.ok) {
            alert(`Succès : Document envoyé !`);
            // Nettoyage des sauvegardes temporaires
            localStorage.removeItem(window.location.pathname);
            const draftID = `DRAFT_${formTitle.replace(/\s+/g, '_')}_${flight}_${dateStr}`;
            localStorage.removeItem(draftID);
            // Retour à l'accueil
            window.location.href = 'index.html';
        } else { 
            alert("Erreur lors de l'envoi au serveur mail."); 
        }
    } catch (e) { 
        console.error(e);
        alert("Erreur technique lors de la génération ou de l'envoi."); 
    }
}

// --- LANCEMENT ---
window.onload = loadSavedData;
document.addEventListener('input', autoSave);