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

    try {
        modMan = new bootstrap.Modal(document.getElementById('modalManual'));
        modRep = new bootstrap.Modal(document.getElementById('modalReplicar'));
    } catch (err) {
        console.error("Erro ao inicializar componentes Bootstrap:", err);
    }
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

// ── SISTEMA DE CONFIRMAÇÃO ASSÍNCRONA (MODAL INTERNO) ──────────
function perguntar(mensagem) {
    return new Promise((resolve) => {
        document.getElementById('modalConfirmacaoTexto').innerText = mensagem;
        const modalEl = document.getElementById('modalConfirmacao');
        const modal = new bootstrap.Modal(modalEl);
        const btnConfirmar = document.getElementById('btnConfirmarModal');
        
        const novoBtn = btnConfirmar.cloneNode(true);
        btnConfirmar.parentNode.replaceChild(novoBtn, btnConfirmar);
        
        novoBtn.addEventListener('click', () => {
            modal.hide();
            resolve(true);
        });
        
        modalEl.addEventListener('hidden.bs.modal', () => {
            resolve(false);
        }, { once: true });
        
        modal.show();
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
    const itens = data.resultados;  // ✅ ADICIONE ESTA LINHA
    
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
    document.getElementById("replicarNovoDia").innerHTML = datasSemana.map((d,i)=>`<option value="${d}">${DIAS[i]}</option>`).join("");
    if(modRep) modRep.show();
}

async function confirmarReplicacao() {
    await fetch("/programacao/adicionar", {
        method: "POST", 
        headers: {"Content-Type":"application/json"},
        body: JSON.stringify({ codigo_cliente: document.getElementById("replicarCodigo").value, data_coleta: document.getElementById("replicarNovoDia").value })
    });
    if(modRep) modRep.hide(); 
    carregarSemana();
}

async function drop(e, dia) {
    e.preventDefault();
    const id = e.dataTransfer.getData("text");
    if(!id) return;
    
    try {
        const res = await fetch(`/programacao/${id}`, {
            method: "PUT",
            headers: {"Content-Type":"application/json"},
            body: JSON.stringify({ data_coleta: dia })
            });
        if(res.ok) {
            carregarSemana();
        } else {
            mostrarToast("Erro ao salvar nova posição do box no servidor.", "danger");
        }
    } catch(err) {
        console.error("Falha ao mover box:", err);
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

document.addEventListener("DOMContentLoaded", () => {
    document.querySelectorAll(".dias-fixos-dropdown").forEach(dropdown => {
        dropdown.addEventListener("hidden.bs.dropdown", async function () {
            const clienteId = this.dataset.clienteId;
            const checkboxes = document.querySelectorAll(`.checkbox-dia-fixo[data-cliente-id="${clienteId}"]:checked`);
            const diasSelecionados = Array.from(checkboxes).map(cb => cb.value);

            // CORREÇÃO 1: Tratando para enviar string vazia se nenhum dia for marcado
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

                // CORREÇÃO 2: Só atualiza a tela se o backend realmente salvou (status 200)
                if (response.ok) {
                    carregarSemana();
                } else {
                    // Se o backend der erro (ex: 400, 404, 500), exibe o erro real no console
                    const erroData = await response.json();
                    console.error("Erro retornado pelo servidor:", erroData);
                    alert("Erro ao salvar: " + (erroData.detail || "Erro desconhecido"));
                }
            } catch (error) {
                // Se o servidor estiver fora do ar ou a rede falhar
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

// ── CONFIRMAR COLETA (REESTRUTURADO SEM POPUPS NATIVOS) ────────
function abrirConfirmar(scheduleId, diaIso) {
    const partes = diaIso.split('-');
    const dataBrPadrao = `${partes[2]}/${partes[1]}/${partes[0]}`;
    
    const input = document.getElementById('inputDataRealColeta');
    input.value = dataBrPadrao;
    
    const modalEl = document.getElementById('modalConfirmarColeta');
    const modal = new bootstrap.Modal(modalEl);
    const btnSalvar = document.getElementById('btnSalvarDataReal');
    
    const novoBtn = btnSalvar.cloneNode(true);
    btnSalvar.parentNode.replaceChild(novoBtn, btnSalvar);
    
    novoBtn.addEventListener('click', async () => {
        const novaData = input.value.trim();
        if (!novaData) return mostrarToast("Por favor, preencha a data.", "warning");
        
        const partesNova = novaData.split('/');
        if (partesNova.length !== 3) {
            mostrarToast("Data inválida. Use o formato DD/MM/AAAA.", "warning");
            return;
        }
        
        const dataConvertida = `${partesNova[2]}-${partesNova[1]}-${partesNova[0]}`;
        modal.hide();
        await salvarConfirmacao(scheduleId, dataConvertida);
    });
    
    modal.show();
}

async function salvarConfirmacao(scheduleId, dataIso) {
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
    await carregarSemana();
}