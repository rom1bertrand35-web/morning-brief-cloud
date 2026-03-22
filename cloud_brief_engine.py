import os
import datetime
import json
import google.generativeai as genai
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

# Configuration
SCOPES = [
    "https://www.googleapis.com/auth/gmail.modify",
    "https://www.googleapis.com/auth/calendar.readonly",
    "https://www.googleapis.com/auth/drive.file",
    "https://www.googleapis.com/auth/documents",
    "https://www.googleapis.com/auth/spreadsheets.readonly",
    "https://www.googleapis.com/auth/analytics.readonly",
    "https://www.googleapis.com/auth/webmasters.readonly", 
    "https://www.googleapis.com/auth/youtube.readonly",
]
DATE_STR = datetime.date.today().strftime("%d/%m/%Y")
DAY_NAME = datetime.date.today().strftime("%A")

def get_google_service(api_name, api_version):
    """Initialise les services Google avec les credentials stockés dans les variables d'environnement."""
    creds_json = os.environ.get('GOOGLE_CREDENTIALS_JSON')
    if not creds_json:
        raise ValueError("La variable d'environnement GOOGLE_CREDENTIALS_JSON est manquante.")
    
    creds_dict = json.loads(creds_json)
    creds = Credentials.from_authorized_user_info(creds_dict, SCOPES)
    
    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())
        
    return build(api_name, api_version, credentials=creds)

def get_previous_topics(drive_service, docs_service):
    """Récupère le contenu des 3 derniers briefs depuis Google Docs pour servir de contexte."""
    print("Recherche des anciens briefs pour le contexte...")
    try:
        results = drive_service.files().list(
            q="name contains 'SALADE_TOMATE_ALGO' and mimeType='application/vnd.google-apps.document'",
            orderBy="createdTime desc",
            pageSize=3,
            fields="files(id, name)"
        ).execute()
        
        items = results.get('files', [])
        topics = ""
        
        for item in items:
            doc = docs_service.documents().get(documentId=item['id']).execute()
            content = ""
            for element in doc.get('body').get('content'):
                if 'paragraph' in element:
                    for run in element.get('paragraph').get('elements'):
                        content += run.get('textRun', {}).get('content', '')
            
            # On prend juste le début (500 caractères) de chaque pour le contexte
            topics += content[:500] + "\n"
            
        return topics
    except Exception as e:
        print(f"Erreur lors de la récupération du contexte: {e}")
        return ""

def run_cloud_brief():
    print(f"🚀 Lancement du Brief Haute Précision CLOUD pour le {DATE_STR}...")
    
    gemini_api_key = os.environ.get("GEMINI_API_KEY")
    if not gemini_api_key:
        raise ValueError("La variable d'environnement GEMINI_API_KEY est manquante.")
        
    genai.configure(api_key=gemini_api_key)
    
    drive_service = get_google_service('drive', 'v3')
    docs_service = get_google_service('docs', 'v1')
    
    prev_context = get_previous_topics(drive_service, docs_service)
    
    prompt = f"""Génère la 'Show Bible' HYPER DÉTAILLÉE de Salade, Tomate, Algorithme du {DATE_STR} ({DAY_NAME}).
    
    ATTENTION : Ce script servira de base à un podcast de 25 à 30 minutes. Le texte généré doit être TRÈS LONG, EXTRÊMEMENT RICHE EN DÉTAILS et ALLER AU FOND DES CHOSES pour chaque sujet. Ne fais pas un simple résumé, mais un véritable script d'émission complet.
    
    EXIGENCE D'ACTUALITÉ : Toutes les informations doivent dater des dernières 24 à 48 heures maximum. Choisis les sujets les plus pertinents et percutants du moment.

    STRUCTURE OBLIGATOIRE DU DOCUMENT :

    1. INTRODUCTION (MANDATORY) :
       - Léa Duchamp et Maxime Verdier se présentent par leur NOM et PRÉNOM.
       - Rappel rapide du concept : 'Le podcast qui mélange IA, Marketing et Actu avec les meilleures sources'.
       - SMALL TALK (Long et détaillé) : Intègre 2 à 3 minutes de conversation spontanée et inédite entre eux sur leur vie, l'actu perso, la météo, ou le fait qu'on soit {DAY_NAME}. Ce doit être DIFFÉRENT chaque jour.

    2. DÉROULÉ PAR RUBRIQUES (SÉPARÉES ET TRÈS FOURNIES) :
       - INSTRUCTION DE RECHERCHE : Fais un scrapping profond de l'actualité brûlante. Utilise des sources ultra-récentes et diversifiées (médias reconnus, comptes officiels, experts vérifiés).
       - IA (50% du temps d'émission) : UN focus majeur de l'actualité immédiate. Explique le fonctionnement EN PROFONDEUR, donne des exemples concrets, cite des déclarations de CEO, analyse les impacts à long terme. Débat entre les présentateurs sur ce sujet.
       - MONDE (10%) : UNE grosse info Géopolitique ou Éco mondiale des dernières 24h. Analyse détaillée des causes et conséquences.
       - MARKET (30%) : UNE campagne virale ou mutation réseaux sociaux du jour. Décortique la stratégie, les chiffres, pourquoi ça marche ou ça floppe.
       - SPORT (10%) : Résultats brûlants de la nuit (NBA, LDC, L1...). Analyse tactique ou focus sur la performance d'un joueur.

    CONTEXTE DE MÉMOIRE (INTERDICTION ABSOLUE DE REPRENDRE CES SUJETS) :
    {prev_context}
    
    RÈGLES D'ÉCRITURE :
    - LONGUEUR : Le texte final doit être très long (viser plus de 2000 mots).
    - Duo LÉA Duchamp & MAXIME Verdier : complices, ils se coupent la parole, rigolent, débattent, se contredisent de manière argumentée.
    - SOURCES : Pour chaque info, cite [Source, DATE précise]. C'est OBLIGATOIRE.
    - OUTRO : Salut l'audience, demande de s'abonner et de liker.
    - ANONYMAT : Ne cite jamais le nom de l'utilisateur.
    """

    try:
        print("🤖 Gemini génère le contenu via CLI...")
        import subprocess
        
        # Le CLI gemini est installé globalement dans l'environnement GitHub
        result = subprocess.run(["gemini", "-p", prompt], capture_output=True, text=True, check=True)
        content = result.stdout

        print("📄 Création du Google Doc...")
        doc = docs_service.documents().create(body={'title': f"SALADE_TOMATE_ALGO - {DATE_STR}"}).execute()
        doc_id = doc.get('documentId')
        
        docs_service.documents().batchUpdate(documentId=doc_id, body={
            'requests': [{'insertText': {'location': {'index': 1}, 'text': content}}]
        }).execute()
            
        print(f"✅ Terminé ! Le brief est disponible ici : https://docs.google.com/document/d/{doc_id}")
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Erreur CLI Gemini : {e.stderr}")
        raise e
    except Exception as e:
        print(f"❌ Erreur lors de l'exécution : {e}")
        raise e

if __name__ == "__main__":
    run_cloud_brief()
