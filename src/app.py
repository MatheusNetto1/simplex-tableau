import streamlit as st
import pulp
import locale

# Configura o locale para formato brasileiro
try:
    locale.setlocale(locale.LC_ALL, 'pt_BR.UTF-8')  # Para Linux/macOS
except:
    locale.setlocale(locale.LC_ALL, '')  # Para Windows

st.title("Solucionador Simplex - Otimização Linear")

# Tipo do problema
tipo = st.radio("Deseja maximizar ou minimizar a função objetivo?", ["Maximizar", "Minimizar"])
tipo_pulp = pulp.LpMaximize if tipo == "Maximizar" else pulp.LpMinimize

# Número de variáveis
num_var = st.slider("Número de variáveis de decisão", min_value=2, max_value=4, step=1)

# Coeficientes da função objetivo
st.subheader("Função Objetivo")
coef_f_obj = []
for i in range(num_var):
    coef = st.number_input(f"Coeficiente de x{i+1}", value=0.0, step=0.1, key=f"obj{i}")
    coef_f_obj.append(coef)

# Número de restrições
num_rest = st.number_input("Quantas restrições?", min_value=1, max_value=10, step=1)

# Entradas das restrições
st.subheader("Restrições")
restricoes = []
for r in range(num_rest):
    st.markdown(f"**Restrição {r+1}**")
    coefs = []
    for i in range(num_var):
        val = st.number_input(f"Coeficiente de x{i+1} (restrição {r+1})", value=0.0, step=0.1, key=f"r{r}_x{i}")
        coefs.append(val)
    operador = st.selectbox("Operador", ["<=", ">=", "="], key=f"op{r}")
    lado_direito = st.number_input("Valor do lado direito", value=0.0, step=0.1, key=f"rhs{r}")
    restricoes.append((coefs, operador, lado_direito))

# Inicializa o histórico no session_state
if "historico" not in st.session_state:
    st.session_state.historico = []

# Botão para resolver
if st.button("Resolver"):
    # Cria problema
    prob = pulp.LpProblem("PPL", tipo_pulp)

    # Variáveis
    variaveis = [pulp.LpVariable(f"x{i+1}", lowBound=0) for i in range(num_var)]

    # Função objetivo
    prob += pulp.lpSum([coef_f_obj[i] * variaveis[i] for i in range(num_var)]), "Função Objetivo"

    # Adiciona restrições
    for idx, (coefs, operador, rhs) in enumerate(restricoes):
        expr = pulp.lpSum([coefs[i] * variaveis[i] for i in range(num_var)])
        if operador == "<=":
            prob += expr <= rhs, f"Restrição {idx+1}"
        elif operador == ">=":
            prob += expr >= rhs, f"Restrição {idx+1}"
        else:
            prob += expr == rhs, f"Restrição {idx+1}"

    # Resolve
    prob.solve()
    status = pulp.LpStatus[prob.status]
    valor_obj = pulp.value(prob.objective) if status == "Optimal" else None
    variaveis_resultado = {var.name: var.varValue for var in prob.variables()}

    # Preços-sombra e folgas
    analise = {}
    if status == "Optimal":
        for nome, restr in prob.constraints.items():
            analise[nome] = {"preco_sombra": restr.pi, "folga": restr.slack}

    # Armazena no histórico
    st.session_state.historico.append({
        "tipo": tipo,
        "coef_obj": coef_f_obj,
        "restricoes": restricoes,
        "status": status,
        "valor_obj": valor_obj,
        "variaveis": variaveis_resultado,
        "analise": analise
    })

    # Resultados
    st.subheader("Resultado Atual")
    if status == "Optimal":
        st.success(f"Solução ótima encontrada!")
        st.markdown(f"**Valor ótimo da função objetivo:** `{locale.currency(valor_obj, grouping=True)}`")
        st.markdown("**Valores das variáveis de decisão:**")
        for nome, val in variaveis_resultado.items():
            st.markdown(f"- `{nome}` = `{locale.currency(val, grouping=True)}`")

        st.subheader("Análise de Sensibilidade")
        for nome, dados in analise.items():
            preco_formatado = locale.currency(dados['preco_sombra'], grouping=True)
            folga_formatada = f"{dados['folga']:.4f}"
            st.markdown(f"- `{nome}` → **Preço-sombra**: `{preco_formatado}` | **Folga**: `{folga_formatada}`")
    elif status == "Infeasible":
        st.error("❌ As restrições fornecidas resultam em um problema **inviável**. Verifique se há contradições.")
    else:
        st.warning(f"Status da solução: `{status}`. Pode não ter sido possível resolver o problema.")

# Mostra histórico
if st.session_state.historico:
    st.subheader("Histórico de Simulações")
    for i, item in enumerate(reversed(st.session_state.historico[-5:])):
        with st.expander(f"Simulação #{len(st.session_state.historico) - i}"):
            st.write(f"Tipo: {item['tipo']}")
            st.write(f"Coeficientes FO: {item['coef_obj']}")
            st.write(f"Status: {item['status']}")
            if item["status"] == "Optimal":
                st.write(f"Valor ótimo: {locale.currency(item['valor_obj'], grouping=True)}")
                for var, val in item["variaveis"].items():
                    st.write(f"{var} = {locale.currency(val, grouping=True)}")

# Botão para limpar histórico
if st.button("Limpar histórico"):
    st.session_state.historico = []
    st.success("Histórico limpo com sucesso!")