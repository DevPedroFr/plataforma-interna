# 📖 Manual de Uso - Plataforma JM

## 1. Acesso ao Sistema

### 1.1 Fazendo Login
1. Acesse o endereço da plataforma no navegador
2. Insira seu **usuário** e **senha** fornecidos pelo administrador
3. Clique em **Entrar**

**[INSERIR PRINT: Tela de login]**

---

## 2. Dashboard Principal

Após o login, você será direcionado ao **Dashboard Principal**, onde visualiza:
- Total de vacinas aplicadas
- Número de pacientes cadastrados  
- Próximos agendamentos do dia
- Alertas de estoque baixo

**[INSERIR PRINT: Dashboard principal com métricas]**

---

## 3. Gerenciamento de Agendamentos

### 3.1 Visualizando o Calendário
1. No menu principal, clique em **Calendário** (ícone de calendário)
2. Visualize os agendamentos por dia, semana ou mês
3. Os agendamentos aparecem com cores diferentes conforme o status:
   - **Agendado** - Aguardando confirmação
   - **Confirmado** - Paciente confirmou presença
   - **Concluído** - Vacina aplicada
   - **Cancelado** - Agendamento cancelado

**[INSERIR PRINT: Tela do calendário com agendamentos]**

### 3.2 Criando um Novo Agendamento
1. No calendário, clique no botão **+ Novo Agendamento**
2. Preencha os dados:
   - **Paciente**: Selecione um paciente existente ou crie um novo
   - **Vacina**: Escolha a vacina a ser aplicada
   - **Data**: Selecione a data do agendamento
   - **Horário**: Escolha o horário disponível
   - **Dose**: Informe qual dose (1ª, 2ª, reforço, etc.)
   - **Observações**: Campo opcional para anotações
3. Clique em **Salvar**

**[INSERIR PRINT: Formulário de criação de agendamento]**

### 3.3 Editando um Agendamento
1. No calendário, clique sobre o agendamento que deseja editar
2. Modifique as informações necessárias
3. Clique em **Atualizar**

**[INSERIR PRINT: Formulário de edição de agendamento]**

### 3.4 Alterando Status do Agendamento
1. Abra o agendamento
2. Altere o campo **Status** para:
   - **Confirmado**: Quando o paciente confirmar presença
   - **Concluído**: Após aplicar a vacina
   - **Cancelado**: Em caso de cancelamento
3. Clique em **Salvar**

### 3.5 Cancelando um Agendamento
1. Abra o agendamento
2. Clique no botão **Excluir** ou **Cancelar**
3. Confirme a ação

---

## 4. Gerenciamento de Pacientes

### 4.1 Visualizando Lista de Pacientes
1. No menu principal, clique em **Pacientes** (ícone de usuários)
2. Visualize a lista completa de pacientes cadastrados
3. Use a barra de busca para encontrar pacientes por nome ou telefone

**[INSERIR PRINT: Lista de pacientes]**

### 4.2 Cadastrando Novo Paciente
1. Na tela de Pacientes, clique em **+ Novo Paciente**
2. Preencha os dados obrigatórios:
   - **Nome completo**
   - **Telefone** (com DDD)
   - **CPF** (opcional)
   - **Data de Nascimento** (opcional)
3. Clique em **Cadastrar**

**[INSERIR PRINT: Formulário de cadastro de paciente]**

### 4.3 Visualizando Histórico do Paciente
1. Na lista de pacientes, clique sobre o nome do paciente
2. Visualize o histórico completo:
   - Vacinas aplicadas anteriormente
   - Agendamentos futuros
   - Última vacina tomada
   - Informações de contato

**[INSERIR PRINT: Detalhes e histórico do paciente]**

---

## 5. Controle de Estoque de Vacinas

### 5.1 Visualizando Estoque
1. No dashboard, a seção de **Estoque** exibe:
   - Vacinas disponíveis
   - Quantidade em estoque
   - Alertas de estoque baixo (quando abaixo do mínimo)

**[INSERIR PRINT: Seção de estoque no dashboard]**

### 5.2 Cadastrando Nova Vacina
1. Acesse a área de **Estoque** ou **Vacinas**
2. Clique em **+ Nova Vacina**
3. Preencha os dados:
   - **Nome da vacina**
   - **Laboratório**
   - **Lote**
   - **Validade**
   - **Quantidade em estoque**
   - **Estoque mínimo** (para alertas)
   - **Preço de compra** (opcional)
   - **Preço de venda** (opcional)
4. Clique em **Salvar**

**[INSERIR PRINT: Formulário de cadastro de vacina]**

### 5.3 Atualizando Estoque
O sistema atualiza automaticamente o estoque quando:
- Uma vacina é aplicada em um agendamento concluído
- O administrador realiza sincronização com o sistema externo

Para atualização manual:
1. Selecione a vacina
2. Clique em **Editar**
3. Altere a quantidade em estoque
4. Clique em **Salvar**

---

## 6. Atendimento via WhatsApp

### 6.1 Visualizando Mensagens
1. No menu, clique em **WhatsApp** (ícone de chat)
2. Visualize todas as conversas ativas
3. Mensagens marcadas como **"Precisa Atendimento Humano"** aparecem em destaque

**[INSERIR PRINT: Tela de mensagens do WhatsApp]**

### 6.2 Respondendo Mensagens
O chatbot responde automaticamente, mas você pode intervir:
1. Selecione a conversa
2. Quando necessário, responda diretamente ao paciente pelo WhatsApp
3. Marque como **Resolvido** após concluir o atendimento

**[INSERIR PRINT: Interface de chat com mensagens]**

### 6.3 Agendamentos via Chatbot
Os pacientes podem agendar pelo WhatsApp. O chatbot:
- Captura dados do paciente
- Oferece horários disponíveis
- Cria o agendamento automaticamente
- Envia confirmação ao paciente

Os agendamentos criados pelo chatbot aparecem no calendário com a marcação **"Via Chatbot"**.

---

## 7. Sincronização com Sistema Externo

### 7.1 Sincronizando Dados
A plataforma sincroniza automaticamente com o sistema GoC (sistema matriz):
- **Agendamentos**: Sincronizados periodicamente
- **Estoque**: Atualizado com base no sistema principal

Para sincronização manual:
1. No dashboard ou calendário, clique em **Sincronizar**
2. Aguarde a confirmação de sincronização concluída

**[INSERIR PRINT: Botão de sincronização e mensagem de sucesso]**

---

## 8. Perfil e Configurações

### 8.1 Acessando seu Perfil
1. Clique no seu nome no canto superior direito
2. Selecione **Perfil**

**[INSERIR PRINT: Menu do usuário]**

### 8.2 Alterando sua Senha
1. No menu do perfil, clique em **Alterar Senha**
2. Digite sua **senha atual**
3. Digite a **nova senha**
4. Confirme a **nova senha**
5. Clique em **Salvar**

**[INSERIR PRINT: Tela de alteração de senha]**

### 8.3 Saindo do Sistema
1. Clique no seu nome no canto superior direito
2. Selecione **Sair**

---

## 9. Dicas e Boas Práticas

### ✅ Recomendações
- **Atualize os status**: Sempre marque os agendamentos como "Concluído" após aplicar a vacina
- **Verifique o estoque**: Confira diariamente os alertas de estoque baixo
- **Confirme agendamentos**: Contate pacientes para confirmar presença
- **Use observações**: Utilize o campo de observações para registrar informações importantes
- **Sincronize regularmente**: Execute sincronizações manuais ao iniciar o expediente

### ⚠️ Alertas Importantes
- Vacinas com **estoque abaixo do mínimo** aparecem destacadas em vermelho
- Mensagens do WhatsApp marcadas como **"Precisa atendimento humano"** requerem ação urgente
- Agendamentos **não confirmados** devem ser verificados até 24h antes da data

---

## 10. Suporte Técnico

Em caso de dúvidas ou problemas técnicos:
- **Email**: suporte@plataformajm.com.br
- **WhatsApp**: (XX) XXXXX-XXXX
- **Horário de atendimento**: Segunda a Sexta, 8h às 18h

---

**Versão do Manual**: 1.0  
**Última atualização**: Janeiro 2026
