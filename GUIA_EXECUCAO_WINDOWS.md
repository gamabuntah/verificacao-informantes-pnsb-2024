# 🚀 GUIA DE EXECUÇÃO - WINDOWS

## ⚠️ **Problema: Erro de Permissões de Rede**

### 🎯 **Sintomas:**
```
Foi feita uma tentativa de acesso a um soquete de uma maneira que é proibida pelas permissões de acesso
WinError 10013: Access is denied
```

---

## 🛠️ **SOLUÇÃO RÁPIDA (3 passos)**

### **Passo 1: Configurar Permissões**
```
1. Clique com BOTÃO DIREITO em: configurar_permissoes_windows.bat
2. Selecione: "Executar como administrador"
3. Aguarde a configuração terminar
```

### **Passo 2: Executar Sistema**
```
1. Clique com BOTÃO DIREITO em: executar_projeto_corrigido.bat  
2. Selecione: "Executar como administrador"
3. Aguarde aparecer: "Running on http://127.0.0.1:5000"
```

### **Passo 3: Acessar no Navegador**
```
1. Abra seu navegador (Chrome, Firefox, Edge)
2. Digite: http://127.0.0.1:5000
3. Pressione ENTER
```

---

## 📋 **ARQUIVOS IMPORTANTES**

| Arquivo | Função | Como Usar |
|---------|--------|-----------|
| `instalar_dependencias_completas.bat` | Instala bibliotecas | Execute 1x apenas |
| `configurar_permissoes_windows.bat` | Configura Windows | Execute como Admin |
| `executar_projeto_corrigido.bat` | Inicia sistema | Execute como Admin |

---

## 🔧 **SE AINDA DER ERRO**

### **1. Verificar Windows Firewall:**
```
1. Windows + R → digite "firewall.cpl" → ENTER
2. Clique em "Permitir um aplicativo pelo Firewall"
3. Clique em "Alterar configurações" 
4. Clique em "Permitir outro aplicativo"
5. Procure e adicione: Python.exe
```

### **2. Verificar Antivírus:**
```
1. Abra seu antivírus (Windows Defender, Avast, etc.)
2. Vá em Configurações → Exclusões
3. Adicione a pasta: C:\Users\ggmob\Cursor AI\Verificação Informantes PNSB
```

### **3. Verificar Porta em Uso:**
```
1. Abra CMD como Administrador
2. Digite: netstat -ano | findstr :5000
3. Se aparecer resultado: taskkill /F /PID [número]
```

---

## ✅ **VERIFICAR SE FUNCIONOU**

### **Sinais de Sucesso:**
```
✅ "Running on http://127.0.0.1:5000"
✅ Navegador abre a página do sistema
✅ Vê a tela de login/dashboard
```

### **URLs para Testar:**
```
http://127.0.0.1:5000          # Página principal
http://127.0.0.1:5000/visitas  # Lista de visitas  
http://127.0.0.1:5000/mapa-progresso  # Mapa de progresso
```

---

## 🆘 **SOLUÇÃO DE EMERGÊNCIA**

Se nada funcionar:

### **1. Reiniciar Tudo:**
```
1. Feche todos os programas
2. Reinicie o computador
3. Execute: configurar_permissoes_windows.bat (como Admin)
4. Execute: executar_projeto_corrigido.bat (como Admin)
```

### **2. Usar Porta Alternativa:**
O sistema tentará automaticamente usar a porta 5001:
```
http://127.0.0.1:5001
```

### **3. Modo Compatibilidade:**
```
1. Clique com botão direito no executar_projeto_corrigido.bat
2. Propriedades → Compatibilidade
3. Marque: "Executar este programa como administrador"
4. Marque: "Executar no modo de compatibilidade para Windows 8"
```

---

## 📞 **SUPORTE TÉCNICO**

### **Informações para Suporte:**
Se precisar de ajuda, forneça:
```
1. Versão do Windows (Windows + R → "winver")
2. Mensagem de erro completa
3. Resultado de: netstat -ano | findstr :5000
4. Se tem antivírus ativo e qual
```

---

## 🎉 **SUCESSO!**

Quando tudo funcionar, você verá:

```
🚀 Iniciando servidor Flask em http://127.0.0.1:5000
📱 Acesse o sistema no seu navegador: http://127.0.0.1:5000
🛑 Para parar o servidor: Pressione CTRL+C
============================================================
 * Running on http://127.0.0.1:5000
```

**O Sistema PNSB 2024 estará funcionando perfeitamente!**