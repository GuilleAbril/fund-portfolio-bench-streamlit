with tab_funds:
    st.markdown("<br>", unsafe_allow_html=True)

    # Cajas de entrada de ISINs
    isins = render_funds_inputs("funds")

    st.markdown("<br>", unsafe_allow_html=True)

    # Inicializar estados en session_state
    if 'last_compared_isins' not in st.session_state:
        st.session_state.last_compared_isins = []
    if 'last_start_date' not in st.session_state:
        st.session_state.last_start_date = None
    if 'last_date_mode' not in st.session_state:
        st.session_state.last_date_mode = None
    if 'should_show_comparison' not in st.session_state:
        st.session_state.should_show_comparison = False
    if 'last_fig' not in st.session_state:
        st.session_state.last_fig = None
    if 'last_html_bytes' not in st.session_state:
        st.session_state.last_html_bytes = None

    compare_fund_button = st.button(
        "Comparar fondos",
        key=f"fund_compare_btn",
        type="primary",
        disabled=not isins or len(isins) == 0,
        width='stretch'
    )

    # Si hay ISINs, mostrar selector de fecha
    if isins and len(isins) > 0:
        start_date = render_funds_date_selector("funds", isins)

        # Obtener el modo de fecha actual
        current_date_mode = st.session_state.get("funds_date_mode", "Usar fecha de inicio común")

        # Detectar cambios
        date_changed = st.session_state.last_start_date != start_date
        date_mode_changed = st.session_state.last_date_mode != current_date_mode
        isins_changed = st.session_state.last_compared_isins != isins

        # Detectar si cambió A un modo automático (no personalizado)
        changed_to_auto_mode = (date_mode_changed and
                                current_date_mode in ["Histórico completo", "Usar fecha de inicio común"])

        # EJECUTAR comparación si:
        should_compare = False

        if compare_fund_button:
            should_compare = True
            st.session_state.should_show_comparison = True
        elif st.session_state.should_show_comparison and date_changed and not date_mode_changed:
            # Solo si la fecha cambió dentro del mismo modo Y no cambiaron los ISINs
            if not isins_changed:
                should_compare = True
        elif st.session_state.should_show_comparison and changed_to_auto_mode:
            # Solo si no cambiaron los ISINs
            if not isins_changed:
                should_compare = True

        # EJECUTAR LA COMPARACIÓN
        if should_compare:
            # Guardar los valores actuales
            st.session_state.last_compared_isins = isins.copy()
            st.session_state.last_start_date = start_date
            st.session_state.last_date_mode = current_date_mode

            st.markdown("<br>", unsafe_allow_html=True)

            # Obtener datos de fondos
            funds_info = get_funds_for_comparison(isins, start_date)

            if not funds_info:
                st.warning("No se pudieron cargar datos de ningún fondo o no hay fechas comunes.")
                st.session_state.last_fig = None
                st.session_state.last_html_bytes = None
            else:
                fig = plot_funds(funds_info, start_date)
                html_bytes = fig.to_html(include_plotlyjs='cdn')

                # GUARDAR en session_state
                st.session_state.last_fig = fig
                st.session_state.last_html_bytes = html_bytes

                # Mostrar
                st.plotly_chart(fig, width='stretch')
                st.download_button(
                    label="Descargar gráfico como HTML",
                    data=html_bytes,
                    file_name="comparador_fondos.html",
                    mime="text/html"
                )

        elif st.session_state.should_show_comparison and st.session_state.last_fig is not None:
            # MOSTRAR LA ÚLTIMA GRÁFICA GUARDADA (sin re-calcular)
            if date_mode_changed:
                st.session_state.last_date_mode = current_date_mode

            st.markdown("<br>", unsafe_allow_html=True)

            # Mostrar la gráfica guardada
            st.plotly_chart(st.session_state.last_fig, width='stretch')
            st.download_button(
                label="Descargar gráfico como HTML",
                data=st.session_state.last_html_bytes,
                file_name="comparador_fondos.html",
                mime="text/html",
                key="download_cached"  # Key diferente para evitar conflicto
            )
        else:
            # Primera vez, antes de pulsar comparar
            st.info("Pulsa 'Comparar fondos' para ver la comparación.")

    else:
        # No hay ISINs
        st.session_state.should_show_comparison = False
        st.info("Añade al menos un fondo para ver la comparación.")
