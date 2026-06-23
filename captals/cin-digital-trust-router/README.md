# CIN Digital Trust Router

Infraestrutura Captals para **validação autorizada, minimização de dados, evidência e replay** em fluxos de identidade digital.

> Não emite, não gera e não simula documento oficial. Não cria QR oficial, não forja assinatura institucional e não substitui serviços governamentais.

## Função correta

```text
Cidadão / Wallet / QR / OIDC autorizado
→ Trust Router
→ Privacy Engine
→ Verification Adapter
→ Audit Ledger encadeado
→ Trust Response
```

A camada atual entrega o núcleo de privacidade e evidência. Adaptadores QR/OIDC e validação de assinatura só podem ser habilitados quando houver conector oficial autorizado e cadeia de confiança verificável.

## Contrato de decisão

O sistema separa assurance de decisão:

| Campo | Significado |
|---|---|
| `status` | estado de assurance: `VALID`, `INVALID`, `EXPIRED`, `REVOKED` ou `UNVERIFIED` |
| `gate` | decisão Captals: `PASS`, `HOLD`, `BLOCK` ou `ESCALATE` |

No modo `sandbox`, uma entrada estruturalmente válida retorna:

```json
{
  "status": "UNVERIFIED",
  "gate": "HOLD",
  "reason": "SANDBOX_NO_OFFICIAL_ASSURANCE"
}
```

Isso é deliberado: o sandbox não pode afirmar autenticidade oficial.

## Garantias implementadas

- Validação algorítmica do CPF exclusivamente em memória volátil.
- HMAC-SHA256 com salt aleatório por sessão.
- Salt com TTL de 15 minutos e consumo único atômico no Redis via `GETDEL`.
- Produção bloqueia operação se o Redis indisponível; não há fallback silencioso para memória.
- Logs cegos: valores e campos sensíveis são redigidos.
- Ledger JSONL com hash SHA-256 canônico, encadeamento `previous_event_hash` e verificação offline.
- Restrições de schema, políticas `allowed`/`blocked` e testes unitários.
- Frontend demonstrativo servido pelo próprio backend, compatível com CSP do Helmet.

## Escopo permitido

- Validar formato de identificador em requisição autorizada.
- Criar sessão efêmera e token de auditoria não reversível.
- Avaliar confiança do emissor configurado.
- Registrar evidência sanitizada.
- Retornar `HOLD` quando assurance oficial não existir.

## Escopo bloqueado

- Emitir RG/CIN ou qualquer documento estatal.
- Criar QR utilizável como documento oficial.
- Forjar assinatura ICP-Brasil ou autoridade emissora.
- Burlar autenticação gov.br, biometria ou controles institucionais.
- Persistir identificador civil bruto em banco, fila, log, arquivo ou ledger.

## Execução local

```bash
cd captals/cin-digital-trust-router
npm install
npm test
npm start
```

Abra o demo em:

```text
http://localhost:3001/demo/
```

Crie uma sessão:

```bash
curl -X POST http://localhost:3001/api/session/start
```

Verifique a integridade do ledger:

```bash
npm run verify:ledger
```

## Docker sandbox

```bash
docker compose up --build
```

O Compose é para sandbox local: expõe o Router apenas em `127.0.0.1:3001`; Redis não é exposto ao host e usa `tmpfs` para que os salts não persistam no disco do host.

## Requisito para `PASS`

O gate só pode se tornar `PASS` quando existir, simultaneamente:

1. integração oficial autorizada;
2. autenticação OIDC/QR válida;
3. assinatura e cadeia de certificado verificadas;
4. emissor e status do documento confirmados;
5. evidência sanitizada e replay verificável.

Sem todos esses elementos, a resposta correta é `HOLD`.

## Modelo Captals

```text
Captals Trust Primitive
= admissibilidade + privacidade + evidência + replay
```
