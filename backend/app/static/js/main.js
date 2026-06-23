const DIAS = ["Segunda", "Terça", "Quarta", "Quinta", "Sexta"];
let datasSemana = [];
let modMan, modRep;

// Recupera a última semana visualizada. Se não houver, assume 0 (Próxima)
let offsetSemana = parseInt(localStorage.getItem("offsetSemana")) || 0;

document.addEventListener("DOMContentLoaded", () => {
    // Fecha semanas passadas automaticamente
    fetch("/fechar-semana", { method: "POST" })
        .then(r => r.json())
        .then(data => {
            if (data.fechado) {
                console.log("Semana fechada:", data.mensagem);
            }
        })
        .catch(e => console.error("Erro ao fechar semana:", e));

    const elMan = document.getElementById('modalManual');
    const elRep = document.getElementById('modalReplicar');

    if (elMan) {
        modMan = bootstrap.Modal.getInstance(elMan) || new bootstrap.Modal(elMan);
    } else {
        console.warn("Aviso: Elemento 'modalManual' não foi encontrado no HTML.");
    }

    if (elRep) {
        modRep = bootstrap.Modal.getInstance(elRep) || new bootstrap.Modal(elRep);
    } else {
        console.warn("Aviso: Elemento 'modalReplicar' não foi encontrado no HTML.");
    }

    // ── CORREÇÃO GLOBAL PARA RESOLVER O ERRO DE ARIA-HIDDEN ──
    // Escuta o evento nativo do Bootstrap disparado quando qualquer modal inicia o fechamento
    document.addEventListener('hide.bs.modal', () => {
        if (document.activeElement) {
            document.activeElement.blur(); // Tira o foco do botão de fechar/X imediatamente
        }
    });
   
    carregarSemana();
    formatarDatasIniciais();
});

// Conjunto de códigos agendados na semana (preenchido ao carregar a grade)
let codigosAgendados = new Set();

// ── SISTEMA DE NOTIFICAÇÕES MODERNAS (TOASTS) ──────────────────
function mostrarToast(mensagem, tipo = 'danger') {
    const container = document.getElementById('toastContainer');
    if (!container) return;

    const bgClass = tipo === 'success' ? 'bg-success' : (tipo === 'warning' ? 'bg-warning text-dark' : 'bg-danger');
    
    const toastHtml = `
        <div class="toast align-items-center text-white ${bgClass} border-0 shadow" role="alert" aria-live="assertive" aria-atomic="true">
            <div class="d-flex">
                <div class="toast-body fw-medium">${mensagem}</div>
                <button type="button" class="btn-close btn-close-white m-auto me-2" data-bs-dismiss="toast" aria-label="Close"></button>
            </div>
        </div>
    `;
    
    const div = document.createElement('div');
    div.innerHTML = toastHtml.trim();
    const toastElement = div.firstChild;
    container.appendChild(toastElement);
    
    const bsToast = new bootstrap.Toast(toastElement, { delay: 4000 });
    bsToast.show();
    
    toastElement.addEventListener('hidden.bs.toast', () => {
        toastElement.remove();
    });
}

// ── SISTEMA DE CONFIRMAÇÃO ASSÍNCRONA CORRIGIDO ──────────
function perguntar(texto) {
    return new Promise((resolve) => {
        // 1. Injeta o texto no modal
        const textoModal = document.getElementById("modalConfirmacaoTexto");
        if (textoModal) textoModal.innerText = texto;

        const modalEl = document.getElementById('modalConfirmacao');
        if (!modalEl) {
            console.error("Modal de confirmação não encontrado no HTML!");
            resolve(false);
            return;
        }

        // Instancia o modal do Bootstrap
        const instanciaModal = bootstrap.Modal.getInstance(modalEl) || new bootstrap.Modal(modalEl);

        // 2. Configura o botão de Confirmar (Garante que resolve como true)
        const btnConfirmar = document.getElementById("btnConfirmarModal");
        if (btnConfirmar) {
            btnConfirmar.onclick = () => {
                // 1. Limpa o foco do botão de fechar ou de confirmar
                if (document.activeElement) document.activeElement.blur(); 
                
                // 2. Esconde o modal
                instanciaModal.hide();
                resolve(true);
            };
        }

        // 3. Configura o fechamento do modal (se fechar no Cancelar ou no X, resolve como false)
        modalEl.addEventListener('hidden.bs.modal', () => {
            resolve(false);
        }, { once: true }); // 'once: true' evita duplicação de eventos nas próximas vezes

        // 4. Remove focos antigos e abre o modal
        if (document.activeElement) document.activeElement.blur();
        instanciaModal.show();
    });
}

function colorirProximasColetas() {
    const hoje = new Date();
    hoje.setHours(0, 0, 0, 0);
    
    document.querySelectorAll('#corpoTabelaClientes tr').forEach(tr => {
        const codigo = tr.getAttribute('data-client-code');
        const tdProxima = tr.querySelector('.td-proxima');
        if (!tdProxima) return;
        
        const span = tdProxima.querySelector('.proxima-texto');
        if (!span) return;
        
        const valorBruto = span.textContent.trim();
        if (!valorBruto || valorBruto === '—') return;
        
        const dataProxima = new Date(valorBruto + 'T00:00:00');
        const formatado = dataProxima.toLocaleDateString('pt-BR');
        
        if (codigo && codigosAgendados.has(codigo)) {
            span.className = 'proxima-agendada';
            span.textContent = '\uD83D\uDCC5 ' + formatado;
        } else if (dataProxima < hoje) {
            span.className = 'proxima-atrasada';
            span.textContent = '\u26A0\uFE0F ' + formatado;
        } else {
            span.className = 'proxima-normal';
            span.textContent = formatado;
        }
    });
}

function atualizarCelulaProxima(clienteId, novaData) {
    const td = document.querySelector('.td-proxima[data-id="' + clienteId + '"]');
    if (!td) return;
    
    const span = td.querySelector('.proxima-texto');
    if (!span) return;
    
    if (!novaData) { 
        span.className = 'proxima-normal'; 
        span.textContent = '—'; 
        return; 
    }
    
    const hoje = new Date(); 
    hoje.setHours(0, 0, 0, 0);
    
    const dataProxima = new Date(novaData + 'T00:00:00');
    const formatado = dataProxima.toLocaleDateString('pt-BR');
    const tr = td.closest('tr');
    const codigo = tr ? tr.getAttribute('data-client-code') : null;
    
    if (codigo && codigosAgendados.has(codigo)) {
        span.className = 'proxima-agendada'; 
        span.textContent = '\uD83D\uDCC5 ' + formatado;
    } else if (dataProxima < hoje) {
        span.className = 'proxima-atrasada'; 
        span.textContent = '\u26A0\uFE0F ' + formatado;
    } else {
        span.className = 'proxima-normal'; 
        span.textContent = formatado;
    }
}

function formatarDatasIniciais() {
    document.querySelectorAll('.data-coleta-input').forEach(input => {
        let v = input.value.trim();
        if (v && v.includes('-')) {
            const parts = v.split('-');
            if (parts.length === 3) {
                input.value = `${parts[2]}/${parts[1]}/${parts[0]}`;
            }
        }
    });
}

async function processarDataExibicao(input, id) {
    let v = input.value.trim();
    if (!v) {
        await salvarCampo(id, 'ultima_coleta', input, '');
        return;
    }
    
    let nums = v.replace(/\D/g, '');
    if (nums.length >= 4) {
        let dia = nums.substring(0, 2).padStart(2, '0');
        let mes = nums.substring(2, 4).padStart(2, '0');
        let ano = '2026';
        
        if (nums.length === 4) { ano = '2026'; } 
        else if (nums.length === 6) { ano = '20' + nums.substring(4, 6); } 
        else if (nums.length >= 8) { ano = nums.substring(4, 8); }
        
        if (parseInt(dia) > 31) dia = '31';
        if (parseInt(mes) > 12) mes = '12';
        
        const exibicaoBR = `${dia}/${mes}/${ano}`;
        const formatoBanco = `${ano}-${mes}-${dia}`;
        
        input.value = exibicaoBR;
        await salvarCampo(id, 'ultima_coleta', input, formatoBanco);
    } else {
        input.classList.add("salvo-erro");
        setTimeout(() => input.classList.remove("salvo-erro"), 1000);
    }
}

async function carregarSemana(offset = null) {
    if (offset !== null) {
        offsetSemana = offset;
        localStorage.setItem("offsetSemana", offsetSemana);
    }
    try {
        const res = await fetch(`/programacao-semana?offset=${offsetSemana}`);
        const data = await res.json();
        datasSemana = data.dias;
        codigosAgendados = new Set();
        Object.values(data.programacao).forEach(coletas => {
            coletas.forEach(c => codigosAgendados.add(c.codigo));
        });
        renderGrade(data);
        colorirProximasColetas();
    } catch(e) {
        console.error("Erro ao carregar dados da semana:", e);
    }
}

function renderGrade(data) {
    const container = document.getElementById("gradeSemana");
    const semanaAtual = data.semana_atual;

    const labels = {
        0: "📅 Próxima Semana",
        "-1": "📋 Semana Atual",
        "-2": "🗂️ Semana Anterior"
    };
    const labelSemana = labels[String(data.offset)] || `Semana (offset ${data.offset})`;

    let html = `
        <div class="grade-header d-flex justify-content-between align-items-center no-print">
            <button class="btn-outline-almeida" onclick="carregarSemana(${data.offset - 1})">← Anterior</button>
            <span style="font-size:0.78rem; font-weight:600; color:var(--verde-escuro)">${labelSemana}</span>
            <button class="btn-outline-almeida" onclick="carregarSemana(${data.offset + 1})">Próxima →</button>
        </div>
        <div class="grade-cols">
    `;

    data.dias.forEach((dia, i) => {
        html += `<div class="col-dia">
            <div class="cabecalho-dia">${DIAS[i]}<br>
            <small>${dia.split('-').reverse().slice(0,2).join('/')}</small></div>
            <div class="corpo-dia" ondragover="event.preventDefault()" ondrop="drop(event, '${dia}')">`;

        const coletas = data.programacao[dia] || [];
        coletas.sort((a, b) => (b.fixo ? 1 : 0) - (a.fixo ? 1 : 0));

        coletas.forEach(c => {
            const concluido = c.status === "Concluído";
            const estilo = concluido ? "opacity:0.6; text-decoration:line-through;" : "";

            html += `<div class="celula-cliente ${c.fixo ? 'fixo' : ''}"
                draggable="true"
                ondragstart="event.dataTransfer.setData('text', ${c.id})"
                style="${estilo}">
                ${c.fixo ? '<span class="fixo-badge">Fixo</span> ' : ''}
                <strong>${c.codigo}</strong> - ${c.cliente}
                <div class="acoes-card no-print">
                    ${semanaAtual && !concluido ? `
                    <button title="Confirmar coleta"
                        onclick="event.stopPropagation(); abrirConfirmar(${c.id}, '${dia}')">✅</button>` : ''}
                    <button title="Replicar"
                        onclick="event.stopPropagation(); abrirReplicar('${c.codigo}')">🔁</button>
                    <button title="Remover"
                        onclick="event.stopPropagation(); excluirColeta(${c.id})">❌</button>
                </div>
            </div>`;
        });

        if (coletas.length === 0) {
            html += `<div class="vazio-dia">Sem coletas</div>`;
        }
        html += `</div></div>`;
    });

    container.innerHTML = html + `</div>`;
}

function alternarModoCadastro(modo) {
    if(modo === 'existente') {
        document.getElementById("blocoClienteExistente").style.display = "block";
        document.getElementById("blocoClienteNovo").style.display = "none";
    } else {
        document.getElementById("blocoClienteExistente").style.display = "none";
        document.getElementById("blocoClienteNovo").style.display = "block";
    }
}

async function filtrarFornecedores() {
    const q = document.getElementById("manualBusca").value;
    const lista = document.getElementById("listaSugestoes");
    if(q.length < 2) return lista.style.display = "none";
    
    const res = await fetch(`/clientes/buscar?q=${encodeURIComponent(q)}`);
    const data = await res.json();
    const itens = data.resultados;
    
    lista.innerHTML = itens.map(i => `
        <div class="list-group-item list-group-item-action py-1 small" 
             style="cursor:pointer;" 
             data-codigo="${i.codigo}" 
             data-nome="${i.nome}" 
             onclick="selecionarBusca(this)">
             <strong>${i.codigo}</strong> | ${i.nome}
        </div>
    `).join("");
    
    lista.style.display = "block";
}

function selecionarBusca(elemento) {
    const codigo = elemento.getAttribute('data-codigo');
    const nome = elemento.getAttribute('data-nome');
    
    const inputCodigo = document.getElementById("manualCodigo");
    const inputBusca = document.getElementById("manualBusca");
    const lista = document.getElementById("listaSugestoes");
    
    if (!inputCodigo || !inputBusca) {
        console.error("ERRO: Elementos não encontrados.");
        mostrarToast("Erro interno ao preencher formulário.", "danger");
        return;
    }
    
    inputCodigo.value = codigo;
    inputBusca.value = nome;
    lista.style.display = "none";
}

function abrirModalManual() {
    document.getElementById("modoExistente").checked = true;
    alternarModoCadastro('existente');
    document.getElementById("manualCodigo").value = "";
    document.getElementById("manualBusca").value = "";
    document.getElementById("manualNovoCodigo").value = "";
    document.getElementById("manualNome").value = "";
    document.getElementById("manualCidade").value = "";
    document.getElementById("manualFrequencia").value = "";
    
    document.getElementById("manualData").innerHTML = datasSemana.map((d,i)=>`<option value="${d}">${DIAS[i]}</option>`).join("");
    if(modMan) modMan.show();
}

async function salvarColetaManual() {
    const btn = document.getElementById("btnSalvarManual");
    const dia = document.getElementById("manualData").value;
    const modoNovo = document.getElementById("modoNovo").checked;
    let codFinal = "";
    
    btn.disabled = true;
    btn.innerText = "Processando...";
    
    try {
        if(modoNovo) {
            codFinal = document.getElementById("manualNovoCodigo").value.trim();
            const nome = document.getElementById("manualNome").value.trim();
            
            if(!codFinal || !nome) {
                mostrarToast("Para novos clientes, o Código e o Nome são obrigatórios.", "warning");
                btn.disabled = false; btn.innerText = "Salvar e Agendar";
                return;
            }
            
            const resCli = await fetch("/clientes/adicionar", {
                method: "POST", 
                headers: {"Content-Type":"application/json"},
                body: JSON.stringify({
                    codigo: codFinal, 
                    nome: nome,
                    cidade: document.getElementById("manualCidade").value.trim(), 
                    frequencia_dias: document.getElementById("manualFrequencia").value || null
                })
            });
            
            if(!resCli.ok) {
                mostrarToast("Incapaz de registrar cliente. Verifique se o código informado já não existe.", "danger");
                btn.disabled = false; btn.innerText = "Salvar e Agendar";
                return;
            }
        } else {
            codFinal = document.getElementById("manualCodigo").value.trim();
            if(!codFinal) {
                mostrarToast("Por favor, busque e selecione um cliente cadastrado da lista.", "warning");
                btn.disabled = false; btn.innerText = "Salvar e Agendar";
                return;
            }
        }
        
        await fetch("/programacao/adicionar", {
            method: "POST", 
            headers: {"Content-Type":"application/json"},
            body: JSON.stringify({ codigo_cliente: codFinal, data_coleta: dia })
        });
        
        if(modMan) modMan.hide();
        location.reload();
    } catch (e) {
        mostrarToast("Falha fatal na comunicação com o sistema.", "danger");
        btn.disabled = false; btn.innerText = "Salvar e Agendar";
    }
}

async function salvarCampo(id, nomeCampo, inputElement, valorCustomizado = undefined) {
    let valor = valorCustomizado !== undefined ? valorCustomizado : inputElement.value;
    let b = {}; 
    b[nomeCampo] = valor;
    
    try {
        const res = await fetch(`/clientes/${id}`, { 
            method: "PUT", 
            headers: {"Content-Type":"application/json"}, 
            body: JSON.stringify(b) 
        });
        
        if(res.ok) {
            const respData = await res.json();
            inputElement.classList.add("salvo-sucesso");
            setTimeout(() => inputElement.classList.remove("salvo-sucesso"), 1000);
            if (respData.proxima_coleta !== undefined) {
                atualizarCelulaProxima(id, respData.proxima_coleta);
            }
        } else {
            inputElement.classList.add("salvo-erro");
        }
    } catch(e) {
        inputElement.classList.add("salvo-erro");
    }
}

function abrirReplicar(cod) {
    document.getElementById("replicarCodigo").value = cod;
    
    const selectDia = document.getElementById("replicarNovoDia");
    if (!selectDia) return;

    if (!datasSemana || datasSemana.length === 0) {
        const diasPadrao = ["Segunda", "Terça", "Quarta", "Quinta", "Sexta"];
        selectDia.innerHTML = diasPadrao.map(dia => `<option value="${dia}">${dia}-feira</option>`).join("");
    } else {
        selectDia.innerHTML = datasSemana.map((d, i) => {
            const dataFormatada = d.split('-').reverse().slice(0, 2).join('/');
            return `<option value="${d}">${DIAS[i]} (${dataFormatada})</option>`;
        }).join("");
    }
    
    const modalEl = document.getElementById('modalReplicar');
    if (modalEl) {
        const modalReplicarInstancia = bootstrap.Modal.getInstance(modalEl) || new bootstrap.Modal(modalEl);
        modalReplicarInstancia.show();
    }
}

async function confirmarReplicacao() {
    const codCliente = document.getElementById("replicarCodigo").value;
    const novaData = document.getElementById("replicarNovoDia").value;

    if (document.activeElement) document.activeElement.blur(); 

    if (!codCliente || !novaData) {
        return mostrarToast("Dados insuficientes para replicar.", "warning");
    }

    try {
        const res = await fetch("/programacao/adicionar", {
            method: "POST", 
            headers: {"Content-Type":"application/json"},
            body: JSON.stringify({ codigo_cliente: codCliente, data_coleta: novaData })
        });

        const modalEl = document.getElementById('modalReplicar');
        if (modalEl) {
            const modalReplicarInstancia = bootstrap.Modal.getInstance(modalEl) || new bootstrap.Modal(modalEl);
            modalReplicarInstancia.hide();
        }

        if (res.ok) {
            mostrarToast("Agendamento replicado com sucesso!", "success");
            await carregarSemana();
        } else {
            mostrarToast("Erro ao replicar no servidor.", "danger");
        }
    } catch (e) {
        mostrarToast("Erro de comunicação ao replicar.", "danger");
    }
}

async function atualizarDiaFixo(id, valor) {
    const checkboxes = document.querySelectorAll(`.checkbox-dia-fixo[data-cliente-id="${id}"]:checked`);
    const diasSelecionados = Array.from(checkboxes).map(cb => cb.value);
    const diaFixoStr = diasSelecionados.join(",");

    await fetch(`/clientes/${id}/fixar`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
            fixo: diasSelecionados.length > 0,
            dia_fixo: diaFixoStr || null
        })
    });
    carregarSemana();
}

// Configuração dos dropdowns de dias fixos
document.addEventListener("DOMContentLoaded", () => {
    document.querySelectorAll(".dias-fixos-dropdown").forEach(dropdown => {
        dropdown.addEventListener("hidden.bs.dropdown", async function () {
            const clienteId = this.dataset.clienteId;
            const checkboxes = document.querySelectorAll(`.checkbox-dia-fixo[data-cliente-id="${clienteId}"]:checked`);
            const diasSelecionados = Array.from(checkboxes).map(cb => cb.value);
            const diasString = diasSelecionados.join(",");

            try {
                const response = await fetch(`/clientes/${clienteId}/fixar`, {
                    method: "PUT",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({
                        fixo: diasSelecionados.length > 0,
                        dia_fixo: diasString 
                    })
                });

                if (response.ok) {
                    carregarSemana();
                } else {
                    const erroData = await response.json();
                    console.error("Erro retornado pelo servidor:", erroData);
                    alert("Erro ao salvar: " + (erroData.detail || "Erro desconhecido"));
                }
            } catch (error) {
                console.error("Falha na rede/requisição:", error);
                alert("Não foi possível conectar ao servidor.");
            }
        });
    });
});

async function gerarProgramacao() { 
    try {
        const res = await fetch("/gerar-programacao", {method:"POST"}); 
        if(res.ok) {
            location.reload(); 
        } else {
            mostrarToast("Erro ao processar a geração automática das coletas.", "danger");
        }
    } catch(e) {
        mostrarToast("Erro de comunicação com o servidor.", "danger");
    }
}

async function fazerUpload() {
    const btn = document.getElementById("btnImportar");
    const f = document.getElementById("inputFile").files[0]; 
    if(!f) return;
    
    btn.disabled = true; 
    btn.innerText = "Enviando...";
    
    const fd = new FormData(); 
    fd.append("file", f);
    
    try { 
        await fetch("/upload", {method:"POST", body:fd}); 
        location.reload(); 
    } catch(e) { 
        mostrarToast("Erro no envio do arquivo.", "danger"); 
        btn.disabled = false; 
        btn.innerText = "Importar Planilha"; 
    }
}

async function excluirColeta(id) { 
    if (await perguntar("Remover esta coleta da semana?")) { 
        const res = await fetch(`/programacao/${id}`, {method:"DELETE"}); 
        if(res.ok) { 
            carregarSemana(); 
            mostrarToast("Coleta removida com sucesso!", "success");
        } else { 
            mostrarToast("Erro ao remover coleta no servidor.", "danger"); 
        }
    } 
}

async function excluirCliente(id, event) { 
    if(event) event.stopPropagation();
    if (await perguntar("Excluir este cliente definitivamente do Banco de Dados?")) { 
        const res = await fetch(`/clientes/${id}`, {method:"DELETE"}); 
        if(res.ok) { 
            location.reload(); 
        } else { 
            mostrarToast("Não foi possível excluir. Motivo: Verifique se este cliente possui coletas ativas registradas na grade.", "warning"); 
        }
    } 
}

function abrirConfirmar(scheduleId, diaIso) {
    const partes = diaIso.split('-');
    const dataBrPadrao = `${partes[2]}/${partes[1]}/${partes[0]}`;
    
    const input = document.getElementById('inputDataRealColeta');
    if (input) {
        if (input.type === 'text') {
            input.value = dataBrPadrao; 
        } else {
            input.value = diaIso; 
        }
    }
    
    const modalEl = document.getElementById('modalConfirmarColeta');
    const modalConfirmar = bootstrap.Modal.getInstance(modalEl) || new bootstrap.Modal(modalEl);
    
    const btnSalvar = document.getElementById('btnSalvarDataReal');
    const novoBtn = btnSalvar.cloneNode(true);
    novoBtn.id = 'btnSalvarDataReal'; 
    btnSalvar.parentNode.replaceChild(novoBtn, btnSalvar);
    
    novoBtn.addEventListener('click', async () => {
        const novaData = input.value.trim();
        if (!novaData) return mostrarToast("Por favor, preencha a data.", "warning");
        
        if (document.activeElement) document.activeElement.blur(); 
        
        if (novaData.includes('-')) {
            modalConfirmar.hide(); 
            await salvarConfirmacao(scheduleId, novaData);
        } else {
            const partesNova = novaData.split('/');
            if (partesNova.length !== 3) {
                return mostrarToast("Data inválida. Use o formato DD/MM/AAAA.", "warning");
            }
            const dataConvertida = `${partesNova[2]}-${partesNova[1]}-${partesNova[0]}`;
            modalConfirmar.hide(); 
            await salvarConfirmacao(scheduleId, dataConvertida);
        }
    });
    
    modalConfirmar.show();
}

async function salvarConfirmacao(scheduleId, dataIso) {
    try {
        const res = await fetch(`/confirmar-coleta/${scheduleId}`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ data_realizada: dataIso })
        });
        
        const data = await res.json();
        
        if (data.erro) {
            mostrarToast(data.erro, "danger");
            return;
        }

        mostrarToast("Coleta confirmada com sucesso!", "success");
        
        // 1. Atualiza a grade de cards da semana (risca o card)
        await carregarSemana();

        // 2. ATUALIZAÇÃO EM TEMPO REAL DA TABELA DE CLIENTES
        // Localiza o card ou botão que disparou a confirmação para achar o código do cliente
        const acaoBotao = document.querySelector(`button[onclick*="abrirConfirmar(${scheduleId}"]`);
        if (acaoBotao) {
            const card = acaoBotao.closest('.celula-cliente');
            if (card) {
                const strongCod = card.querySelector('strong');
                if (strongCod) {
                    const codigoCliente = strongCod.textContent.trim();
                    
                    // Encontra a linha correta do cliente na tabela inferior
                    const trTabela = document.querySelector(`#corpoTabelaClientes tr[data-client-code="${codigoCliente}"]`);
                    if (trTabela) {
                        
                        // A) Atualiza o campo "Última Coleta" (Input)
                        const inputUltima = trTabela.querySelector('.data-coleta-input');
                        if (inputUltima) {
                            const partes = dataIso.split('-');
                            inputUltima.value = `${partes[2]}/${partes[1]}/${partes[0]}`;
                            
                            // Efeito visual verde de sucesso no campo
                            inputUltima.classList.add("salvo-sucesso");
                            setTimeout(() => inputUltima.classList.remove("salvo-sucesso"), 1000);
                        }
                        
                        // B) Atualiza a coluna "Próxima Coleta" baseada na resposta do servidor
                        // Se o servidor retornar null, limpamos a célula. Se retornar uma data, atualiza.
                        const clienteId = trTabela.querySelector('.td-proxima')?.getAttribute('data-id');
                        if (clienteId) {
                            atualizarCelulaProxima(clienteId, data.proxima_coleta_calculada);
                        }
                    }
                }
            }
        }

    } catch (e) {
        console.error("Erro ao confirmar coleta:", e);
        mostrarToast("Erro de comunicação ao confirmar a coleta.", "danger");
    }
}

// ── SISTEMA DE ARRASTAR E SOLTAR (DRAG AND DROP) ──────────────────

async function drop(ev, novoDiaFormatado) {
    ev.preventDefault();
    const idColeta = ev.dataTransfer.getData("text");
    
    if (!idColeta || !novoDiaFormatado) {
        console.error("Dados inválidos no drop.");
        return;
    }

    console.log(`Movendo coleta ID ${idColeta} para o dia ${novoDiaFormatado}`);

    try {
        const res = await fetch(`/programacao/${idColeta}`, {
            method: "PUT",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                data_coleta: novoDiaFormatado
            })
        });

        if (res.ok) {
            mostrarToast("Coleta movida com sucesso!", "success");
            await carregarSemana(); 
        } else {
            console.error("Erro na resposta do servidor:", res.status);
            mostrarToast("Não foi possível mover a coleta.", "danger");
        }
    } catch (error) {
        console.error("Erro na requisição do drop:", error);
        mostrarToast("Erro de conexão ao mover a coleta.", "danger");
    }
}

function hojeISO() {
  return new Date().toISOString().slice(0, 10);
}

function showToast(msg, tipo = "success") {
  // usa o toast já existente no projeto, se disponível
  if (typeof exibirToast === "function") { exibirToast(msg, tipo); return; }
  const cor = tipo === "success" ? "#25D366" : tipo === "danger" ? "#ef4444" : "#2563eb";
  const div = document.createElement("div");
  div.textContent = msg;
  Object.assign(div.style, {
    position:"fixed", bottom:"24px", right:"24px", zIndex:"9999",
    background: cor, color:"#fff", padding:"10px 20px",
    borderRadius:"10px", fontWeight:"600", fontSize:".85rem",
    boxShadow:"0 4px 16px rgba(0,0,0,.18)", transition:"opacity .3s"
  });
  document.body.appendChild(div);
  setTimeout(() => { div.style.opacity="0"; setTimeout(() => div.remove(), 400); }, 3000);
}

// ─── IMPORTAR PROGRAMAÇÃO ────────────────────────────────────
async function importarProgramacao() {
  const input = document.getElementById("inputProgramacao");
  if (!input || !input.files.length) {
    showToast("Selecione um arquivo CSV ou Excel de programação.", "warning");
    return;
  }
  const form = new FormData();
  form.append("file", input.files[0]);

  try {
    const resp = await fetch("/importar-programacao", { method: "POST", body: form });
    const data = await resp.json();

    if (resp.ok) {
      showToast(`✅ Importado com sucesso!`, "success");

      if (data.texto_whatsapp) {
        const modalEl = document.getElementById("modalWhatsApp");
        const waTexto = document.getElementById("waTexto");
        const waContador = document.getElementById("waContador");
        const waDataLabel = document.getElementById("waDataLabel");

        if (waTexto) waTexto.value = data.texto_whatsapp;
        if (waContador) waContador.textContent = `${data.texto_whatsapp.length} caracteres`;
        if (waDataLabel) waDataLabel.textContent = "Gerado da planilha importada";

        if (modalEl) {
          const modal = new bootstrap.Modal(modalEl);
          modal.show();
        }
      }
    } else {
      showToast("Erro: " + (data.detail || "Falha na importação"), "danger");
    }
  } catch (e) {
    showToast("Erro de conexão: " + e.message, "danger");
  }
  input.value = "";
}

// ─── MODAL WHATSAPP ──────────────────────────────────────────
function abrirModalWhatsApp() {
  const input = document.getElementById("waData");
  if (!input.value) input.value = hojeISO();
  document.getElementById("waTexto").value = "";
  document.getElementById("waContador").textContent = "0 caracteres";
  document.getElementById("waDataLabel").textContent = "";
  const modal = new bootstrap.Modal(document.getElementById("modalWhatsApp"));
  modal.show();
  // já gera automaticamente com a data de hoje
  buscarMensagemWhatsApp();
}

async function buscarMensagemWhatsApp() {
  const dataVal = document.getElementById("waData").value;
  if (!dataVal) { showToast("Selecione uma data.", "warning"); return; }

  const labelEl = document.getElementById("waDataLabel");
  labelEl.textContent = "⏳ Carregando...";

  try {
    const resp = await fetch(`/programacao/whatsapp?data=${dataVal}`);
    const json = await resp.json();
    if (resp.ok) {
      const area = document.getElementById("waTexto");
      area.value = json.texto;
      document.getElementById("waContador").textContent = json.texto.length + " caracteres";
      labelEl.textContent = `Programação de ${json.data}`;
    } else {
      showToast("Erro ao gerar mensagem: " + (json.detail || ""), "danger");
      labelEl.textContent = "";
    }
  } catch (e) {
    showToast("Erro de conexão: " + e.message, "danger");
    document.getElementById("waDataLabel").textContent = "";
  }
}

async function copiarMensagemWhatsApp() {
  const texto = document.getElementById("waTexto").value;
  if (!texto || texto.startsWith("PROGRAMAÇÃO") === false) {
    showToast("Gere a mensagem antes de copiar.", "warning");
    return;
  }
  try {
    await navigator.clipboard.writeText(texto);
    showToast("✅ Mensagem copiada! Cole no WhatsApp.", "success");
  } catch {
    // fallback para browsers antigos
    document.getElementById("waTexto").select();
    document.execCommand("copy");
    showToast("✅ Mensagem copiada!", "success");
  }
}

// atualizar contador ao editar manualmente
document.addEventListener("DOMContentLoaded", function () {
  const area = document.getElementById("waTexto");
  const contador = document.getElementById("waContador");

  if (area && contador) {
    area.addEventListener("input", function () {
      contador.textContent = area.value.length + " caracteres";
    });
  }
});