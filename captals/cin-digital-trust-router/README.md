# CIN Digital Trust Router

Infraestrutura segura para validação federada de CIN/identidade digital no escopo Captals.

Este projeto **não emite**, **não gera** e **não simula documento oficial**. Ele opera como camada de confiança: valida formato, sessão, QR/OIDC autorizado, emissor, assinatura/status quando houver conector oficial e registra evidência sem armazenar CPF bruto.

## Função correta

```text
Cidadão / Wallet / QR / OIDC
→ Trust Router
→ Privacy Engine
→ Verification Engine
→ Audit Ledger
→ Trust Response
```

## Escopo permitido

- Validação algorítmica de CPF em memória volátil.
- Tokenização efêmera por sessão com HMAC-SHA256.
- Salt de sessão em Redis com TTL e consumo one-time.
- Logs cegos com redaction de CPF.
- Ledger auditável sem coluna/campo `cpf`.
- Schemas JSON para resposta de confiança e evento de auditoria.
- Sandbox frontend demonstrativo.
- CI com testes e scanner de termos proibidos.

## Escopo bloqueado

- Gerar RG/CIN oficial.
- Criar QR oficial utilizável.
- Forjar assinatura ICP-Brasil.
- Bypass gov.br/OIDC.
- Simular autoridade estatal.
- Persistir CPF bruto em banco, fila, log, arquivo ou evento.

## Execução local

```bash
cd captals/cin-digital-trust-router
cp .env.example .env
npm install
npm test
npm start
```

Com Docker:

```bash
docker compose up --build
```

API local:

```bash
curl -X POST http://localhost:3001/api/session/start
```

Use o `sessionId` retornado:

```bash
curl -X POST http://localhost:3001/api/cin/validate \
  -H 'Content-Type: application/json' \
  -d '{"sessionId":"SESSION_ID_AQUI","cpf":"111.444.777-35","issuerState":"SP"}'
```

## Resposta esperada

```json
{
  "status": "VALID",
  "issuer": {
    "country": "BR",
    "state_code": "SP",
    "agency_id": "SANDBOX-SP-001"
  },
  "verification": {
    "cpf_format_valid": true,
    "issuer_trusted": true,
    "signature_valid": false,
    "source": "sandbox"
  },
  "audit": {
    "audit_id": "uuid",
    "transaction_id": "uuid",
    "audit_token_hash": "sha256hex",
    "recorded": true
  }
}
```

## Política de dados

O CPF existe apenas durante a execução da função de validação/tokenização. O sistema retorna e armazena apenas hash de auditoria. O ledger rejeita qualquer evento que contenha padrão de CPF.

## Modelo Captals

Esta infraestrutura se encaixa como:

```text
Captals Trust Primitive
= admissibilidade + privacidade + evidência + replay
```

Estados recomendados:

- `PASS`: validação autorizada, sem dados sensíveis persistidos.
- `HOLD`: conector oficial indisponível ou resposta parcial.
- `BLOCK`: tentativa de emissão/forja/bypass/persistência indevida.
- `ESCALATE`: ambiguidade jurídica, incidente ou suspeita de fraude.
