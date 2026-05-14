# Tracking — página de teste manual

Página única (`tracking_test.html`) com 3 telas: login Cognito, modo
INSPECTOR (envia GPS) e modo ADMIN (vê live + histórico).

## Pré-requisitos

1. PRs #45/#46/#47/#48/#49 mergeados e a Lightsail provisionada com o
   ws_server rodando (live via WS).
2. PR #50 mergeado e o endpoint serverless `GET /mss-formularios/tracking/history`
   deployado (necessário só pra carregar histórico).
3. Static IP da Lightsail anotado (ex: `54.232.10.5`).
4. URL base do API Gateway anotada (ex: `https://abc.execute-api.sa-east-1.amazonaws.com/dev/mss-formularios`).
5. Cognito **App Client com `USER_PASSWORD_AUTH` habilitado**:
   - Console → User Pool → App integration → seu app client →
     "Authentication flows" → marcar `ALLOW_USER_PASSWORD_AUTH`.
6. 1 user `INSPECTOR` e 1 user `ADMIN` cadastrados no User Pool +
   Profile registrado na tabela de Profiles.

## Como rodar

```bash
cd tests/manual
python -m http.server 8000
# abre http://localhost:8000/tracking_test.html
```

Browser geolocation API exige HTTPS **ou** localhost — `localhost:8000` funciona.

## Fluxo de teste end-to-end

1. **Login** (na sidebar):
   - Stage: `dev`
   - Static IP: o que você anotou (usado pra `wss://...sslip.io`)
   - API Gateway base URL: ex `https://abc.execute-api.sa-east-1.amazonaws.com/dev/mss-formularios` (usado pra `/tracking/history`)
   - Region: `sa-east-1`
   - Client ID: do app client Cognito
   - Email/senha do user INSPECTOR
   - Botão "Login" → JWT obtido

2. **Aba INSPECTOR** → "▶ Iniciar localização":
   - Browser pede permissão de GPS — aceita
   - WS conecta (status fica verde)
   - Lat/lng/precisão atualizam a cada movimento (ou parado, conforme `watchPosition`)
   - Pings vão pro DDB e fan-out pros admins
   - Pode levar o laptop pra rua, ou abrir no celular (mesma URL via IP local)

3. **"⏹ Parar"** quando terminar.

4. **Faz logout e login de novo com o user ADMIN**.

5. **Aba ADMIN** → "▶ Conectar ao live":
   - Snapshot inicial pinta inspectors online no mapa
   - Eventos `connect`/`disconnect`/`location` atualizam markers e polylines em tempo real

6. **Aba ADMIN → seção "Histórico"**:
   - Cole o `user_id` do inspector (sub do JWT do user INSPECTOR — o login
     já preenche o seu próprio sub por default)
   - Datetime de "desde" e "até" (default: últimas 12h)
   - "📍 Carregar rota" → polyline laranja desenha a rota completa do
     período escolhido (mesmo que o inspector já esteja offline)

## Notas

- A página é **só pra teste manual**, não vai pra prod. Salva token só na
  memória da aba (sem localStorage).
- Cores dos markers/polylines são geradas por hash do `user_id` — útil
  pra distinguir vários inspectors simultâneos.
- Histórico é uma camada laranja tracejada separada dos markers live, então
  você pode ter os 2 ao mesmo tempo no mapa.
