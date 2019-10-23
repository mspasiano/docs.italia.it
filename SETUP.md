# Setup dell'ambiente di sviluppo locale

0. Recuperare il codice da git con il modulo common

    ```bash
    git clone git@github.com:italia/docs.italia.it.git
    cd docs.italia.it
    git submodule update --init --recursive
    ```

1. Creare il file `.secrets` inserendo le seguenti variabili d'ambiente valorizzate con le credenziali di produzione, da richiedere agli amministratori di Docs Italia*:

    ```ini
    GITHUB_API_SECRET=
    SLUMBER_PASSWORD=
    ```

2. Modificare il file `/etc/hosts` di sistema aggiungendo:

    ```h
    127.0.0.1   local.docs.italia.it
    ::1         local.docs.italia.it
    ```

3. Effettuare il setup di Docker e aggiungere il db da un dump in formato `dump.sql[.bz2|.gz]`, da richiedere agli amministratori di Docs Italia*.

    **WARNING**: *Docker avrà necessità di poter allocare memoria sufficiente per far girare tutti i container. Qualora in qualche fase della procedura uno o più container terminasse improvvisamente con status code `137`, è possibile che la quantità di RAM utilizzabile da docker sia troppo limitata, e sia pertanto necessario configurare la propria installazione per consentire un uso maggiore di memoria.*

    **WARNING**: *Gli step successivi sono stati testati con docker in versione `18.09.7` e superiori e docker-compose in versione `1.21.0`. e superiore su sistemi OSX e Ubuntu GNU/Linux*

    ```bash
    docker-compose build
    ./docker/db_restore.sh /path/to/dump.sql
    docker-compose up
    ```

4. Verificare il login nella URL http://local.docs.italia.it/admin/ usando *devadmin* come username *pippo* come password.

5. Per far funzionare l'integrazione con GitHub bisogna creare una applicazione OAuth a questo indirizzo: https://github.com/settings/applications/new e utilizzare i seguenti parametri:

    - inserire ciò che si preferisce in "Application name"
    - inserire "http://local.docs.italia.it" in "Homepage URL"
    - inserire una descrizione per la vostra applicazione OAuth, che faccia riferimento al vostro ambiente locale di Docs Italia
    - inserire "http://local.docs.italia.it/accounts/github/login/callback/" in "Authorization callback URL"

6. Dall'admin Django nella app `Social Accounts`, model `Social applications` aggiungere una nuova istanza:
    1. selezionare "Github" in "Provider"
    2. inserire "local" come "Name"
    3. inserire in "Client id" inserire il "Client ID" generato su GitHub nel punto 5
    4. inserire in "Secret key" inserire il "Client Secret" generato su GitHub nel punto 5
    5. selezionare "local.docs.italia.it" come "Sites"

    In caso di problemi, verificare che:

    - il dominio del site Django, quello con cui si accede per il login e quello indicato come callback URL siano identici (anche con lo stesso protocollo)
    - il setting ACCOUNT_DEFAULT_HTTP_PROTOCOL corrisponda al protocollo (http o https) effettivamente usato nella propria istanza (default: http)
    - esista una ed una sola applicazione GitHub per il Site #1; nel caso si cancelli un'applicazione social, cancellerà anche tutti i token associati, confermare la cancellazione.

7. Visitare la URL a http://local.docs.italia.it/ , se necessario fare logout dall'utente `devadmin` e verificare che il login tramite GitHub

    **NOTE**: *il link di verifica indirizzo email appare tra i log in console (non viene eseguito alcun invio reale).*

8. Create empty indexes:

    ```bash
    ./docker/create_indices.sh
    ```

9. Collegarsi alla URL http://local.docs.italia.it/dashboard/ e verificare che l'import dei repository funzioni correttamente seguendo i seguenti passaggi:

    1. Premere il button **Import a Project**
    2. Premere il button **🔄**
    3. Premere il button **+** di fianco al repository da importare
    4. Premere il button **Builds**
    5. Verificare che la build termini correttamente

10. Verificare che la funzionalità di ricerca funzione visitando ad esempio questa URL http://local.docs.italia.it/search/?q=documento

_* per contattarci, puoi scriverci sul canale `#docs-italia-software` dello [Slack di Developers Italia](https://slack.developers.italia.it/) o aprire una issue su questo repo._
