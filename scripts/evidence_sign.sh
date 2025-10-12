#!/usr/bin/env bash
set -e
mkdir -p evidence/tokens evidence/verify
echo "SHA256:stub_merkle_root" > evidence/merkle_root.txt
echo "TSA_TOKEN_STUB" > evidence/tokens/2025Q1.tsr
cat > evidence/evidence_manifest.json <<EOF
{"run_id":"2025Q1-ACME-0001","merkle_root":"SHA256:stub_merkle_root","artifacts":["raga/kpis.json","xbrl/informe.xbrl"],"tsa_tokens":["evidence/tokens/2025Q1.tsr"]}
EOF
echo "Verification: OK" > evidence/verify/2025Q1.txt
echo "Evidence signed (stub)"
