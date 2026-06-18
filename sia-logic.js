/**
 * SIA LOGIC CENTRALISÉE
 * Gère : Majuscules, Auto-save, Brouillons, Chargement et Envoi PDF
 */

// --- CONFIGURATION ET ÉLÉMENTS ---
var selectVol = document.getElementById('flight-select') || document.querySelector('.select-vol');
const volDisplay = document.getElementById('vol-display');
const dateInput = document.getElementById('date-input') || document.getElementById('dateMain') || document.querySelector('.input-date-calendar');
const formToPrint = document.getElementById('form-to-print') || document.getElementById('pdf');
const formTitle = document.title || "DOCUMENT_SIA";

// --- 1. GESTION DES MAJUSCULES AUTOMATIQUES ---
document.addEventListener('input', (e) => {
    if ((e.target.tagName === 'INPUT' && e.target.type !== 'date') || e.target.tagName === 'TEXTAREA') {
        e.target.value = e.target.value.toUpperCase();
    }
});

// --- 2. MISE À JOUR DU VOL ---
if (selectVol && volDisplay) {
    selectVol.addEventListener('change', (e) => {
        volDisplay.textContent = e.target.value;
    });
}

// --- 3. SAUVEGARDE AUTOMATIQUE ---
function autoSave() {
    const formData = {};
    document.querySelectorAll('input, select, textarea').forEach((el, index) => {
        const key = el.id || el.name || `field_${index}`;
        formData[key] = (el.type === 'checkbox' || el.type === 'radio') ? el.checked : el.value;
    });
    localStorage.setItem(window.location.pathname, JSON.stringify(formData));
}

// --- 4. CHARGEMENT DES DONNÉES ---
function loadSavedData() {
    const resumeData = localStorage.getItem("RESUME_DATA");
    const autoSavedData = localStorage.getItem(window.location.pathname);
    const data = resumeData ? JSON.parse(resumeData) : (autoSavedData ? JSON.parse(autoSavedData) : null);

    if (data) {
        document.querySelectorAll('input, select, textarea').forEach((el, index) => {
            const key = el.id || el.name || `field_${index}`;
            if (data[key] !== undefined) {
                if (el.type === 'checkbox' || el.type === 'radio') el.checked = data[key];
                else el.value = data[key];
            }
        });

        if (resumeData) localStorage.removeItem("RESUME_DATA");
        if (selectVol && volDisplay) volDisplay.textContent = selectVol.value;
    }
}

// --- 5. SAUVEGARDE BROUILLON ---
function saveDraft() {
    const flight = selectVol ? selectVol.value : "REF";
    const date = dateInput ? dateInput.value : "SANS-DATE";
    const draftID = `DRAFT_${formTitle.replace(/\s+/g, '_')}_${flight}_${date}`;

    if (localStorage.getItem(draftID)) {
        if (!confirm("Un brouillon existe déjà.\nÉcraser la sauvegarde actuelle ?")) return;
    }

    const formData = {};
    document.querySelectorAll('input, select, textarea').forEach((el, index) => {
        const key = el.id || el.name || `field_${index}`;
        formData[key] = (el.type === 'checkbox' || el.type === 'radio') ? el.checked : el.value;
    });

    localStorage.setItem(draftID, JSON.stringify({
        type: formTitle,
        url: window.location.pathname,
        date: new Date().toLocaleString(),
        data: formData
    }));

    alert("Brouillon sauvegardé !");
}

// --- 6. ENVOI PDF + MAIL ---
async function saveAndSend() {
    if (!formToPrint) {
        alert("Erreur: Conteneur d'impression non trouvé.");
        return;
    }

    const flight = selectVol ? selectVol.value : "SIA";
    const dateStr = dateInput ? dateInput.value : "SANS-DATE";
    const fileName = `${formTitle.replace(/\s+/g, '_')}_${flight}_${dateStr}.pdf`;
    const isManifest = document.title.includes("BAGAGE MANIFEST");

const opt = {
    margin: 0,
    filename: fileName,
    image: { type: 'jpeg', quality: 1 },
    html2canvas: {
        scale: isManifest ? 1.4 : 2,
        useCORS: true,
        scrollX: 0,
        scrollY: 0,
        x: 0,
        y: 0,
        onclone: function (clonedDoc) {
            const clonedForm = clonedDoc.getElementById('form-to-print');
            if (clonedForm && isManifest) {
                clonedForm.style.position = 'absolute';
                clonedForm.style.top = '0';
                clonedForm.style.left = '0';
                clonedForm.style.margin = '0';
            }
            clonedDoc.body.style.margin = '0';
            clonedDoc.body.style.padding = '0';
        }
    },
    jsPDF: {
        unit: 'mm',
        format: 'a4',
        orientation: isManifest ? 'landscape' : 'portrait'
    },
    pagebreak: { mode: ['css', 'legacy'] }
};
    try {
        html2pdf().set(opt).from(formToPrint).save();

        const pdfBlob = await html2pdf().set(opt).from(formToPrint).output('blob');

        const formData = new FormData();
        formData.append('pdf', pdfBlob, fileName);
        formData.append('filename', fileName);
        formData.append('subject', `${formTitle} - ${flight} - ${dateStr}`);
        formData.append('body', `Veuillez trouver ci-joint le document ${formTitle}.`);

        const response = await fetch("https://doc-sq.onrender.com/send-pdf", {
            method: 'POST',
            body: formData
        });

        const responseText = await response.text();
        console.log("SEND PDF STATUS:", response.status);
        console.log("SEND PDF RESPONSE:", responseText);

        if (response.ok) {
            alert("Succès : Document envoyé !");
            localStorage.removeItem(window.location.pathname);

            const draftID = `DRAFT_${formTitle.replace(/\s+/g, '_')}_${flight}_${dateStr}`;
            localStorage.removeItem(draftID);

            window.location.href = 'index.html';
        } else {
            alert("Erreur mail : " + response.status + "\n" + responseText);
        }

    } catch (e) {
        console.error(e);
        alert("Erreur technique lors de la génération ou de l'envoi.");
    }
}

// --- LANCEMENT ---
window.onload = loadSavedData;
document.addEventListener('input', autoSave);
