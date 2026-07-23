
-- ============================================================
-- Add remaining missing variable definitions
-- ============================================================
INSERT INTO variable_definitions (name, placeholder, description, type, category, is_required, default_value, display_order)
VALUES
  -- Rede / Domínio
  ('DC_SECUNDARIO_IP',  '{{DC_SECUNDARIO_IP}}',  'IP do controlador de dominio secundario (opcional)',                'text',    'dominio',     FALSE, '',          120),
  ('OM_NAME',           '{{OM_NAME}}',            'Nome completo da organizacao (ex: Comando da Aeronautica)',         'text',    'branding',    FALSE, '',          121),
  ('SEEDER_SERVER',     '{{SEEDER_SERVER}}',      'URL do servidor SeederLinux para o agente (ex: https://seeder.om.local)', 'text', 'agente', TRUE,  '',          122),
  -- Ambiente grafico
  ('DISPLAY_MANAGER',   '{{DISPLAY_MANAGER}}',    'Gerenciador de login: lightdm, gdm3 ou sddm',                      'select',  'ambiente',    FALSE, 'lightdm',   123),
  ('INSTALL_DESKTOP',   '{{INSTALL_DESKTOP}}',    'Instalar ambiente grafico? Se false, usa o ja instalado',          'boolean', 'ambiente',    FALSE, 'false',     124),
  -- Aplicativos
  ('INSTALL_CHROME',    '{{INSTALL_CHROME}}',     'Instalar Google Chrome?',                                          'boolean', 'aplicacoes',  FALSE, 'true',      125),
  ('INSTALL_CHROMIUM',  '{{INSTALL_CHROMIUM}}',   'Instalar Chromium?',                                               'boolean', 'aplicacoes',  FALSE, 'false',     126),
  ('INSTALL_ONLYOFFICE','{{INSTALL_ONLYOFFICE}}', 'Instalar OnlyOffice Desktop Editors?',                             'boolean', 'aplicacoes',  FALSE, 'true',      127),
  -- Segurança / Legacy
  ('JAVA_EXCEPTIONS',   '{{JAVA_EXCEPTIONS}}',    'Excecoes de seguranca Java: lista de URLs autorizadas (uma por linha)', 'array', 'seguranca', FALSE, '',         128),
  -- SSH
  ('SSH_PORT',          '{{SSH_PORT}}',           'Porta SSH (padrao: 22)',                                            'text',    'acesso_remoto', FALSE, '22',      129),
  ('SSH_GROUPS',        '{{SSH_GROUPS}}',         'Grupos AD com acesso SSH (separados por espaco)',                   'text',    'acesso_remoto', FALSE, '',        130)
ON CONFLICT (name) DO NOTHING;

-- Seed values for all organizations
INSERT INTO organization_variables (organization_id, variable_id, value)
SELECT o.id, vd.id, vd.default_value
FROM organizations o
CROSS JOIN variable_definitions vd
WHERE vd.name IN (
  'DC_SECUNDARIO_IP','OM_NAME','SEEDER_SERVER','DISPLAY_MANAGER','INSTALL_DESKTOP',
  'INSTALL_CHROME','INSTALL_CHROMIUM','INSTALL_ONLYOFFICE','JAVA_EXCEPTIONS',
  'SSH_PORT','SSH_GROUPS'
)
ON CONFLICT (organization_id, variable_id) DO NOTHING;
