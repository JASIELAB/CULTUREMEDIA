# --- Sección: Soluciones Stock ---
elif choice == "Soluciones Stock":
    st.header("🧪 Gestionar Soluciones Stock")
    col1, col2 = st.columns(2)
    with col1:
        fecha_sol = st.date_input("Fecha", value=date.today())
        cantidad_sol = st.number_input("Cantidad (L)", min_value=0.0, format="%.2f")
        codigo_sol = st.text_input("Código Solución")
    with col2:
        responsable = st.text_input("Responsable")
        regulador = st.text_input("Regulador")
        observaciones = st.text_area("Observaciones")
    if st.button("Registrar solución"):
        # Añadimos al DataFrame y guardamos
        sol_df.loc[len(sol_df)] = [
            fecha_sol.isoformat(),
            cantidad_sol,
            codigo_sol,
            responsable,
            regulador,
            observaciones
        ]
        sol_df.to_csv(SOL_FILE, index=False)
        mov_df.loc[len(mov_df)] = [
            datetime.now().isoformat(),
            "Stock Solución",
            codigo_sol,
            cantidad_sol,
            f"Resp: {responsable}"
        ]
        mov_df.to_csv(HIST_FILE, index=False)
        st.success(f"Solución {codigo_sol} registrada.")

    st.markdown("---")
    st.subheader("📋 Inventario de Soluciones")
    st.dataframe(sol_df, use_container_width=True)
    st.download_button(
        "Descargar Soluciones (CSV)",
        sol_df.to_csv(index=False).encode("utf-8"),
        file_name="soluciones_stock.csv"
    )

# --- Sección: Control del Sistema ---
elif choice == "Control del Sistema":
    st.header("⚙️ Control del Sistema")

    # 1) Editar inventario de lotes
    st.subheader("Editar Inventario de Lotes")
    inv_edit = st.experimental_data_editor(inv_df, num_rows="dynamic")
    if st.button("Guardar cambios inventario"):
        inv_edit.to_csv(INV_FILE, index=False)
        st.success("Inventario actualizado.")

    st.markdown("---")
    # 2) Eliminar lote
    st.subheader("Eliminar Lote")
    cod_elim = st.selectbox("Selecciona código de lote", inv_df["Código"].tolist())
    if st.button("Eliminar lote"):
        inv_df.drop(inv_df[inv_df["Código"] == cod_elim].index, inplace=True)
        inv_df.to_csv(INV_FILE, index=False)
        st.success(f"Lote {cod_elim} eliminado.")

    st.markdown("---")
    # 3) Editar soluciones
    st.subheader("Editar Soluciones Stock")
    sol_edit = st.experimental_data_editor(sol_df, num_rows="dynamic")
    if st.button("Guardar cambios soluciones"):
        sol_edit.to_csv(SOL_FILE, index=False)
        st.success("Soluciones stock actualizadas.")

    st.markdown("---")
    # 4) Eliminar solución
    st.subheader("Eliminar Solución")
    cod_sol_elim = st.selectbox("Código solución", sol_df["Código_Solución"].tolist())
    if st.button("Eliminar solución"):
        sol_df.drop(sol_df[sol_df["Código_Solución"] == cod_sol_elim].index, inplace=True)
        sol_df.to_csv(SOL_FILE, index=False)
        st.success(f"Solución {cod_sol_elim} eliminada.")
