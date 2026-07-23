
-- ============================================================
-- 1. Replace decorative {{VARIAVEL}} comment text in all scripts
-- ============================================================
UPDATE scripts
SET content = replace(content, '{{VARIAVEL}}', 'VARIAVEL')
WHERE content LIKE '%{{VARIAVEL}}%';

-- ============================================================
-- 2. Replace {{INSTALL_LEGADOS}} with 'false' (deprecated var)
-- ============================================================
UPDATE scripts
SET content = replace(content, '{{INSTALL_LEGADOS}}', 'false')
WHERE content LIKE '%{{INSTALL_LEGADOS}}%';

-- ============================================================
-- 3. Add missing variable definitions
-- ============================================================
INSERT INTO variable_definitions (name, placeholder, description, type, category, is_required, default_value, display_order)
VALUES
  ('REMOVER_LIBREOFFICE',  '{{REMOVER_LIBREOFFICE}}',  'Remover LibreOffice pre-instalado',                      'boolean', 'aplicacoes', FALSE, 'false', 116),
  ('INSTALL_LEGADOS',      '{{INSTALL_LEGADOS}}',       'Instalar sistemas legados (Java 8, Firefox 52.7 ESR)',    'boolean', 'aplicacoes', FALSE, 'true',  117),
  ('INSTALL_AGENT',        '{{INSTALL_AGENT}}',         'Instalar agente de check-in periodico (seeder-agent)',   'boolean', 'agente',     FALSE, 'true',  118),
  ('AGENT_NO_CHECK_CERT',  '{{AGENT_NO_CHECK_CERT}}',   'Permitir certificado autoassinado no agente (--no-check-certificate)', 'boolean', 'agente', FALSE, 'true', 119)
ON CONFLICT (name) DO NOTHING;

-- ============================================================
-- 4. Seed values for all organizations (using default_value)
-- ============================================================
INSERT INTO organization_variables (organization_id, variable_id, value)
SELECT o.id, vd.id, vd.default_value
FROM organizations o
CROSS JOIN variable_definitions vd
WHERE vd.name IN ('REMOVER_LIBREOFFICE', 'INSTALL_LEGADOS', 'INSTALL_AGENT', 'AGENT_NO_CHECK_CERT')
ON CONFLICT (organization_id, variable_id) DO NOTHING;
