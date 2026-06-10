const DIAS = ["Segunda", "Terça", "Quarta", "Quinta", "Sexta"];
let datasSemana = [];
let modMan, modRep;
let offsetSemana = 0; // 0=próxima, -1=atual, -2=anterior



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

    // resto do código existente...
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

// CORREÇÃO E FORMATADOR DA DATA BRASILEIRA COM SALVAMENTO CONVERTIDO
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
        
        // Deixa visível em formato brasileiro para o usuário
        input.value = exibicaoBR;
        
        // Dispara o salvamento enviando a conversão aceita pelo Python SQL
        await salvarCampo(id, 'ultima_coleta', input, formatoBanco);
    } else {
        input.classList.add("salvo-erro");
        setTimeout(() => input.classList.remove("salvo-erro"), 1000);
    }
}

async function carregarSemana(offset = null) {
    if (offset !== null) offsetSemana = offset;
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

    // Label da semana
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
    const itens = await res.json();
    
    // Mudamos o onclick para passar o elemento inteiro (this) 
    // e guardamos os dados de forma segura em data-attributes
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
    // Recupera os dados guardados de forma segura
    const codigo = elemento.getAttribute('data-codigo');
    const nome = elemento.getAttribute('data-nome');
    
    const inputCodigo = document.getElementById("manualCodigo");
    const inputBusca = document.getElementById("manualBusca");
    const lista = document.getElementById("listaSugestoes");
    
    // Alerta de segurança caso faltar algum ID no HTML
    if (!inputCodigo || !inputBusca) {
        console.error("ERRO: Os inputs 'manualCodigo' ou 'manualBusca' não foram encontrados no HTML.");
        alert("Erro interno: Campos de texto não encontrados no formulário.");
        return;
    }
    
    // Preenche os campos e esconde a lista
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
                alert("Para novos clientes, o Código e o Nome são obrigatórios.");
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
                alert("Incapaz de registrar cliente. Verifique se o código informado já não existe.");
                btn.disabled = false; btn.innerText = "Salvar e Agendar";
                return;
            }
        } else {
            codFinal = document.getElementById("manualCodigo").value.trim();
            if(!codFinal) {
                alert("Por favor, busque e selecione um cliente cadastrado da lista.");
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
        alert("Falha fatal na comunicação com o sistema.");
        btn.disabled = false; btn.innerText = "Salvar e Agendar";
    }
}

// SALVAR EDIÇÕES DIRETAS NA TABELA
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

// FUNÇÃO DRAG AND DROP CORRIGIDA PARA ATUALIZAR E SALVAR NO SISTEMA IMEDIATAMENTE
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
            carregarSemana(); // Recarrega a grade com a alteração salva no banco
        } else {
            alert("Erro ao salvar nova posição do box no servidor.");
        }
    } catch(err) {
        console.error("Falha ao mover box:", err);
    }
}

async function atualizarDiaFixo(id, valor) {
    // Coleta todos os checkboxes marcados para este cliente
    const checkboxes = document.querySelectorAll(
        `.checkbox-dia-fixo[data-cliente-id="${id}"]:checked`
    );
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

            const checkboxes = document.querySelectorAll(
                `.checkbox-dia-fixo[data-cliente-id="${clienteId}"]:checked`
            );

            const diasSelecionados = Array.from(checkboxes).map(cb => cb.value);

            await fetch(`/clientes/${clienteId}/fixar`, {
                method: "PUT",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({
                    fixo: diasSelecionados.length > 0,
                    dia_fixo: diasSelecionados.join(",") || null
                })
            });

            carregarSemana();
        });

    });

});

async function gerarProgramacao() { 
    try {
        const res = await fetch("/gerar-programacao", {method:"POST"}); 
        if(res.ok) {
            location.reload(); 
        } else {
            alert("Erro ao processar a geração automática das coletas.");
        }
    } catch(e) {
        alert("Erro de comunicação com o servidor.");
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
        alert("Erro no envio do arquivo."); 
        btn.disabled = false; 
        btn.innerText = "Importar Planilha"; 
    }
}

async function excluirColeta(id) { 
    if(confirm("Remover esta coleta da semana?")) { 
        const res = await fetch(`/programacao/${id}`, {method:"DELETE"}); 
        if(res.ok) { carregarSemana(); } else { alert("Erro ao remover coleta no servidor."); }
    } 
}

async function excluirCliente(id, event) { 
    if(event) event.stopPropagation();
    if(confirm("Excluir este cliente definitivamente do Banco de Dados?")) { 
        const res = await fetch(`/clientes/${id}`, {method:"DELETE"}); 
        if(res.ok) { 
            location.reload(); 
        } else { 
            alert("Não foi possível excluir. Motivo: Verifique se este cliente possui coletas ativas registradas na grade."); 
        }
    } 
}

// ── CONFIRMAR COLETA ───────────────────────────────────────
function abrirConfirmar(scheduleId, diaIso) {
    const dataFormatada = diaIso; // YYYY-MM-DD
    const confirmou = confirm(
        `Confirmar coleta realizada em ${diaIso.split('-').reverse().join('/')}?\n\nClique OK para confirmar ou Cancelar para informar outra data.`
    );

    if (confirmou) {
        salvarConfirmacao(scheduleId, dataFormatada);
    } else {
        const novaData = prompt(
            "Informe a data real da coleta (DD/MM/AAAA):",
            diaIso.split('-').reverse().join('/')
        );
        if (!novaData) return;

        // Converte DD/MM/AAAA para YYYY-MM-DD
        const partes = novaData.split('/');
        if (partes.length !== 3) return alert("Data inválida.");
        const dataConvertida = `${partes[2]}-${partes[1]}-${partes[0]}`;
        salvarConfirmacao(scheduleId, dataConvertida);
    }
}

async function salvarConfirmacao(scheduleId, dataIso) {
    const res = await fetch(`/confirmar-coleta/${scheduleId}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ data_realizada: dataIso })
    });
    const data = await res.json();
    if (data.erro) return alert(data.erro);
    await carregarSemana();
}