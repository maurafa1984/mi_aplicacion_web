import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
import streamlit as st
print("--- PASO 1: Streamlit importado ---")
import requests
print("--- PASO 2: Requests importado ---")
import os
print("--- PASO 3: OS importado ---")

# Configuración de la URL de la API
API_URL = st.secrets.get("API_URL", "https://mi_aplicacion_web.onrender.com")
print(f"--- PASO 4: URL de la API configurada: {API_URL} ---")

# --- MENÚ DE NAVEGACIÓN ---
st.sidebar.title("Navegación")
opciones = [
    "Inicio", 
    "Ver Inventario", 
    "Crear Producto", 
    "Gestión Avanzada (Editar/Eliminar)", 
    "Ver Licencias por ID",
    "Cargar Licencias",  
    "Editar Licencia",
    "Gestión de Ventas",
]
menu = st.sidebar.selectbox("Selecciona una opción", opciones)

# --- LÓGICA DE LAS OPCIONES ---

if menu == "Inicio":
    st.title("Panel Administrativo")
    st.write("Bienvenido al sistema de gestión de TechCommerce.")

elif menu == "Ver Inventario":
    st.header("📦 Inventario Actual")
    try:
        res = requests.get(f"{API_URL}/productos", verify=False)
        if res.status_code == 200:
            st.table(res.json())
        else:
            st.error("No se pudo cargar el inventario.")
    except Exception as e:
        st.error(f"Error de conexión con la API: {e}")

elif menu == "Crear Producto":
    st.header("➕ Crear Nuevo Producto")
    with st.form("form_crear"):
        nombre = st.text_input("Nombre")
        precio = st.number_input("Precio", min_value=0.0)
        categoria = st.selectbox("Categoría", ["Hardware", "Software"])
        stock = st.number_input("Stock", min_value=0, step=1)
        
        if st.form_submit_button("Guardar Producto"):
            payload = {"nombre": nombre, "precio": precio, "categoria": categoria, "stock": stock}
            res = requests.post(f"{API_URL}/productos/", json=payload,verify=False) # Asegúrate de la barra final si tu API la requiere
            
            # Aceptamos tanto 200 como 201
            if res.status_code in [200, 201]:
                st.success("Producto creado correctamente")
            else:
                st.error(f"Error al crear producto: {res.status_code}")

elif menu == "Gestión Avanzada (Editar/Eliminar)":
    st.header("⚙️ Gestión de Productos")
    pid = st.number_input("Ingresa ID del Producto para cargar datos:", min_value=1, step=1)
    
    if "producto_a_editar" not in st.session_state:
        st.session_state.producto_a_editar = None

    if st.button("Cargar Datos del Producto"):
        res = requests.get(f"{API_URL}/productos/{int(pid)}", verify=False)
        if res.status_code == 200:
            st.session_state.producto_a_editar = res.json()
            st.success(f"Producto cargado: {res.json()['nombre']}")
        else:
            st.error("Producto no encontrado")

    if st.session_state.producto_a_editar:
        prod = st.session_state.producto_a_editar
        with st.form("form_editar"):
            st.subheader(f"Editando ID {pid}: {prod['nombre']}")
            n_nombre = st.text_input("Nuevo Nombre", value=prod['nombre'])
            n_precio = st.number_input("Nuevo Precio", value=float(prod['precio']))
            categorias = ["Hardware", "Software"]
            idx = categorias.index(prod['categoria']) if prod['categoria'] in categorias else 0
            n_cat = st.selectbox("Nueva Categoría", categorias, index=idx)
            n_stock = st.number_input("Nuevo Stock", value=int(prod['stock']))
            
            if st.form_submit_button("Confirmar Cambios"):
                payload = {"nombre": n_nombre, "precio": n_precio, "categoria": n_cat, "stock": n_stock}
                res = requests.put(f"{API_URL}/productos/{pid}", json=payload, verify=False)
                if res.status_code == 200:
                    st.success("¡Producto actualizado exitosamente!")
                    st.session_state.producto_a_editar = None
                else:
                    st.error("Error al actualizar")

    st.divider()
    if st.button("❌ ELIMINAR ESTE PRODUCTO"):
        res = requests.delete(f"{API_URL}/productos/{int(pid)}", verify=False)
        if res.status_code == 200:
            st.warning("Producto eliminado permanentemente")
            st.session_state.producto_a_editar = None
        else:
            st.error("Error al intentar eliminar")

elif menu == "Ver Licencias por ID":
    st.header("🔑 Consultar Licencias por ID")
    pid_licencia = st.number_input("Ingresa el ID del producto:", min_value=1, step=1)
    if st.button("Consultar Licencias"):
        res_prod = requests.get(f"{API_URL}/productos/{int(pid_licencia)}")
        if res_prod.status_code == 200:
            producto = res_prod.json()
            st.subheader(f"Producto: {producto['nombre']}")
            res_claves = requests.get(f"{API_URL}/productos/{int(pid_licencia)}/claves")
            if res_claves.status_code == 200:
                claves = res_claves.json()
                if claves:
                    for c in claves:
                        st.success(f"Licencia: `{c['codigo']}`")
                        st.write(f"Detalle: {c['descripcion']}")
                else:
                    st.info("No hay licencias registradas.")
            else:
                st.error("No se pudieron cargar las licencias.")
        else:
            st.error("Producto no encontrado.")

elif menu == "Cargar Licencias":
    st.header("📤 Cargar Nueva Licencia")
    with st.form("form_cargar_licencia"):
        id_producto = st.number_input("ID del Producto", min_value=1, step=1)
        codigo = st.text_input("Código de Licencia")
        descripcion = st.text_input("Descripción (Ej: Windows 11 Pro)")
        
        if st.form_submit_button("Registrar Licencia"):
            payload = {"producto_id": id_producto, "codigo": codigo, "descripcion": descripcion}
            # Cambia la línea de la petición para asegurarte de usar la barra final
            res = requests.post(f"{API_URL}/productos/{id_producto}/claves/", json=payload, verify=False)
            
            
            if res.status_code in [200, 201]:
                st.success("¡Licencia registrada con éxito!")
            else:
                # Esto te ayudará a ver qué está pasando si vuelve a fallar
                st.error(f"Error al registrar la licencia (Código {res.status_code}): {res.text}")

elif menu == "Editar Licencia":
    st.header("✏️ Editar Licencia")
    # Necesitas pedir ambos IDs porque tu API no tiene un endpoint global de claves
    pid = st.number_input("ID del Producto:", min_value=1, step=1)
    lic_id = st.number_input("ID de la Licencia a editar:", min_value=1, step=1)
    
    if st.button("Buscar Licencia"):
        res = requests.get(f"{API_URL}/productos/{pid}/claves", verify=False)
        if res.status_code == 200:
            claves = res.json()
            # Muestra los IDs disponibles para que el usuario sepa cuáles existen
            ids_disponibles = [item.get('id', 'N/A') for item in claves]
            st.info(f"IDs encontrados para este producto: {ids_disponibles}")
            
            # Buscamos la licencia seleccionada
            licencia = next((item for item in claves if str(item.get('id')) == str(lic_id)), None)
            
            if licencia:
                st.session_state.licencia_a_editar = licencia
            else:
                st.error("No se encontró esa licencia. Verifica el ID en la lista de arriba.")
        else:
            st.error("Error al conectar con la API.")

    if "licencia_a_editar" in st.session_state and st.session_state.licencia_a_editar:
        lic = st.session_state.licencia_a_editar
        with st.form("form_editar_licencia"):
            nuevo_codigo = st.text_input("Nuevo Código", value=lic['codigo'])
            nueva_desc = st.text_input("Nueva Descripción", value=lic['descripcion'])
            
            if st.form_submit_button("Guardar Cambios"):
                # IMPORTANTE: Si tu API no tiene PUT /productos/{pid}/claves/{lic_id},
                # este paso fallará. ¿Tu API tiene un PUT para editar claves?
                payload = {"codigo": nuevo_codigo, "descripcion": nueva_desc}
                res = requests.put(f"{API_URL}/productos/{pid}/claves/{lic_id}", json=payload)
                if res.status_code in [200, 201]:
                    st.success("¡Licencia actualizada!")
                    st.session_state.licencia_a_editar = None
                else:
                    st.error(f"Error: {res.status_code} - {res.text}")

elif menu == "Gestión de Ventas":
    st.header("🛒 Gestión de Ventas")
    
    tab1, tab2 = st.tabs(["Registrar Venta", "Ver Historial y Facturas"])

    with tab1:
        with st.form("venta_form"):
            prod_id = st.number_input("ID del Producto", min_value=1, step=1)
            cantidad = st.number_input("Cantidad", min_value=1, step=1)
            enviar = st.form_submit_button("Confirmar Venta")
            
            if enviar:
                response = requests.post(f"{API_URL}/ventas/", json={"producto_id": int(prod_id), "cantidad": int(cantidad)})
                if response.status_code == 201:
                    st.success("¡Venta registrada con éxito!")
                else:
                    st.error(f"Error: {response.json().get('detail')}")

    with tab2:
        st.subheader("Historial de Ventas")
        res = requests.get(f"{API_URL}/ventas/", verify=False)
        if res.status_code == 200:
            ventas = res.json()
            for v in ventas:
                with st.container():
                    col1, col2 = st.columns([3, 1])
                    col1.write(f"**Venta #{v['id']}** | Prod ID: {v['producto_id']} | Cant: {v['cantidad']} | Total: ${v['total']}")
                    
                    if col2.button("🧾 Facturar", key=f"fact_{v['id']}"):
                        res_fact = requests.get(f"{API_URL}/ventas/{v['id']}/factura")
                        if res_fact.status_code == 200:
                            factura = res_fact.json()
                            st.success("Factura generada:")
                            st.write(f"**ID Factura:** {factura['factura_id']}")
                            st.write(f"**Producto:** {factura['producto_nombre']}")
                            st.write(f"**Cantidad:** {factura['cantidad']}")
                            st.write(f"**Total:** ${factura['total_pagado']}")
                        else:
                            st.error(f"Error: {res_fact.status_code} - {res_fact.text}")
        else:
            st.info("No hay ventas para mostrar.")