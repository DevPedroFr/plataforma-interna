import time
import re
import logging
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from .base_scraper import BaseScraper


class PatientSearchScraper(BaseScraper):
    """Busca paciente no sistema legado por CPF na página Paciente.aspx."""

    def __init__(self, browser_manager):
        super().__init__(browser_manager)
        self.patients_url = "https://aruja.gocfranquias.com.br/Cadastro/Paciente.aspx"
        # Inicializa o logger
        self.logger = logging.getLogger(__name__)

    def _format_cpf(self, cpf: str) -> str:
        digits = re.sub(r"\D", "", cpf or "")
        if len(digits) != 11:
            return cpf or ""
        return f"{digits[0:3]}.{digits[3:6]}.{digits[6:9]}-{digits[9:11]}"

    def _wait_for_ajax(self, timeout=10):
        """Aguarda a conclusão de requisições AJAX."""
        try:
            WebDriverWait(self.browser.driver, timeout).until(
                lambda d: d.execute_script("return jQuery.active == 0")
            )
        except:
            pass  # Continua mesmo se jQuery não estiver disponível

    def search_by_cpf(self, cpf: str):
        """
        Realiza a busca por CPF e retorna o primeiro resultado da grade (se existir).

        Retorno:
            {
              'name': str,
              'birth_date': str,
              'register_date': str,
              'responsible1': Optional[str],
              'responsible2': Optional[str],
              'cpf': str
            }
            ou None se não encontrar.
        """
        if not self.ensure_login():
            print("Falha no login")
            return None

        # Navega para a página de pacientes
        print(f"Navegando para: {self.patients_url}")
        self.browser.driver.get(self.patients_url)

        try:
            # Aguarda a grid carregar
            WebDriverWait(self.browser.driver, 20).until(
                EC.presence_of_element_located((By.ID, "ctl00_ContentPlaceHolder1_GridView1"))
            )
            print("Grid de pacientes carregada")
        except TimeoutException:
            print("Timeout aguardando grid de pacientes")
            return None

        # Localiza campo de CPF no filtro - baseado nos dados do POST
        cpf_value = self._format_cpf(cpf)
        print(f"Buscando CPF: {cpf_value}")

        try:
            # PRIMEIRO: Limpar filtros anteriores
            self._clear_all_filters()
            
            # SEGUNDO: Encontrar o campo de CPF no filtro
            cpf_input = WebDriverWait(self.browser.driver, 10).until(
                EC.presence_of_element_located((By.ID, "ctl00_ContentPlaceHolder1_GridView1_ctl01_fltCPF"))
            )
            
            # TERCEIRO: Preencher o campo CPF
            cpf_input.clear()
            time.sleep(0.3)
            
            # Usar ActionChains para enviar caracteres um por um (importante para campos mascarados)
            actions = ActionChains(self.browser.driver)
            actions.click(cpf_input)
            
            # Enviar Backspace várias vezes para limpar completamente
            for _ in range(20):
                actions.send_keys(Keys.BACKSPACE)
            
            # Enviar o CPF caractere por caractere
            for char in cpf_value:
                actions.send_keys(char)
                time.sleep(0.05)
            
            actions.perform()
            time.sleep(0.5)
            
            print(f"CPF '{cpf_value}' inserido no campo")
            
            # QUARTO: Clicar no botão Filtrar usando JavaScript
            # Encontrar o botão de filtrar (pode ser por ID ou por imagem)
            filter_button = None
            
            # Tentar pelo ID primeiro
            try:
                filter_button = self.browser.driver.find_element(
                    By.ID, "ctl00_ContentPlaceHolder1_GridView1_ctl01_BtnFiltrar"
                )
            except:
                # Tentar pelo src da imagem
                try:
                    filter_button = self.browser.driver.find_element(
                        By.CSS_SELECTOR, "input[src*='find.png']"
                    )
                except:
                    # Tentar pelo título
                    try:
                        filter_button = self.browser.driver.find_element(
                            By.CSS_SELECTOR, "input[title*='Filtrar']"
                        )
                    except:
                        pass
            
            if filter_button:
                print("Clicando no botão Filtrar via JavaScript")
                # Usar JavaScript para clicar (mais confiável)
                self.browser.driver.execute_script("arguments[0].click();", filter_button)
            else:
                print("Botão Filtrar não encontrado, tentando Enter")
                cpf_input.send_keys(Keys.RETURN)
            
            # Aguarda processamento - tempo extra para ASP.NET WebForms
            print("Aguardando processamento do filtro...")
            time.sleep(3)
            
            # Aguardar animação/loading
            self._wait_for_ajax(8)
            
            # Verificar se houve atualização da grid
            try:
                WebDriverWait(self.browser.driver, 10).until(
                    EC.presence_of_element_located((By.ID, "ctl00_ContentPlaceHolder1_GridView1"))
                )
                print("Grid atualizada após filtro")
            except:
                print("Grid não parece ter sido atualizada")
            
        except (TimeoutException, NoSuchElementException) as e:
            print(f"Erro ao interagir com campo CPF: {e}")
            # Tentar abordagem alternativa
            return self._alternative_search_by_cpf(cpf_value)

        # Coleta resultados
        return self._extract_results(cpf_value)

    def _clear_all_filters(self):
        """Limpa todos os campos de filtro para garantir busca limpa."""
        try:
            print("Limpando filtros anteriores...")
            
            # Encontrar todos os campos de input na linha de filtro
            filter_inputs = self.browser.driver.find_elements(
                By.CSS_SELECTOR, 
                "#ctl00_ContentPlaceHolder1_GridView1 tr.Grid input[type='text']"
            )
            
            for input_field in filter_inputs:
                try:
                    input_field.clear()
                except:
                    pass
            
            # Também limpar selects
            filter_selects = self.browser.driver.find_elements(
                By.CSS_SELECTOR,
                "#ctl00_ContentPlaceHolder1_GridView1 tr.Grid select"
            )
            
            for select_field in filter_selects:
                try:
                    self.browser.driver.execute_script("arguments[0].selectedIndex = 0;", select_field)
                except:
                    pass
            
            time.sleep(1)
            
        except Exception as e:
            print(f"Erro ao limpar filtros: {e}")

    def _alternative_search_by_cpf(self, cpf_value):
        """Abordagem alternativa usando JavaScript para enviar o formulário completo."""
        try:
            print("Tentando abordagem alternativa com JavaScript completo")
            
            # Script JavaScript para preencher CPF e submeter o formulário
            script = f"""
            // 1. Encontrar e limpar o campo CPF
            var cpfInput = document.getElementById('ctl00_ContentPlaceHolder1_GridView1_ctl01_fltCPF');
            if (!cpfInput) {{
                return 'cpf_input_not_found';
            }}
            
            // 2. Limpar o campo
            cpfInput.value = '';
            
            // 3. Configurar o valor do CPF
            cpfInput.value = '{cpf_value}';
            
            // 4. Disparar eventos para campos mascarados
            var event = new Event('input', {{ bubbles: true }});
            cpfInput.dispatchEvent(event);
            
            var changeEvent = new Event('change', {{ bubbles: true }});
            cpfInput.dispatchEvent(changeEvent);
            
            // 5. Encontrar o botão Filtrar
            var filterBtn = document.getElementById('ctl00_ContentPlaceHolder1_GridView1_ctl01_BtnFiltrar');
            if (!filterBtn) {{
                // Tentar encontrar pela imagem
                filterBtn = document.querySelector('input[src*="find.png"]');
            }}
            
            if (filterBtn) {{
                // 6. Submeter o formulário
                filterBtn.click();
                return 'filter_clicked';
            }} else {{
                // 7. Tentar submeter via __doPostBack
                __doPostBack('ctl00$ContentPlaceHolder1$GridView1$ctl01$BtnFiltrar', '');
                return 'postback_triggered';
            }}
            """
            
            result = self.browser.driver.execute_script(script)
            print(f"Resultado do JS: {result}")
            
            # Aguardar processamento
            time.sleep(4)
            self._wait_for_ajax(10)
            
            return self._extract_results(cpf_value)
            
        except Exception as e:
            print(f"Erro na abordagem alternativa: {e}")
            return None

    def _extract_results(self, cpf_value):
        """Extrai resultados da grid após a filtragem."""
        try:
            # Aguarda mais tempo para garantir que a grid foi atualizada
            print("Aguardando atualização completa da grid...")
            time.sleep(2)
            
            # Verifica se há mensagem de "Nenhum registro encontrado"
            try:
                no_records = self.browser.driver.find_elements(
                    By.XPATH, 
                    "//td[contains(text(), 'Nenhum registro encontrado') or contains(text(), 'Nenhum registro')]"
                )
                if no_records:
                    print("Nenhum registro encontrado na busca")
                    return None
            except:
                pass

            # Tentar encontrar linhas com o CPF específico
            print(f"Procurando por linhas com CPF: {cpf_value}")
            
            # Primeiro, tenta encontrar pelo CPF na linha
            cpf_clean = re.sub(r'\D', '', cpf_value)
            rows_with_cpf = []
            
            # Procura em todas as linhas da tabela
            all_rows = self.browser.driver.find_elements(
                By.CSS_SELECTOR,
                "#ctl00_ContentPlaceHolder1_GridView1 tr"
            )
            
            for row in all_rows:
                try:
                    row_text = row.text
                    # Verifica se o CPF está na linha
                    if cpf_value in row_text or cpf_clean in row_text:
                        rows_with_cpf.append(row)
                        print(f"Encontrada linha com CPF: {row_text[:100]}")
                except:
                    continue
            
            # Se encontrou linhas com o CPF, usa a primeira
            if rows_with_cpf:
                print(f"Encontradas {len(rows_with_cpf)} linha(s) com o CPF")
                row = rows_with_cpf[0]
            else:
                # Se não encontrou, procura por qualquer linha de dados
                print("CPF não encontrado nas linhas, procurando primeira linha de dados...")
                
                # Localizar a grid
                grid = WebDriverWait(self.browser.driver, 10).until(
                    EC.presence_of_element_located((By.ID, "ctl00_ContentPlaceHolder1_GridView1"))
                )
                
                # Encontrar linhas de dados (que não são cabeçalho ou filtro)
                data_rows = []
                all_trs = grid.find_elements(By.TAG_NAME, "tr")
                
                for tr in all_trs:
                    try:
                        # Ignorar linhas de cabeçalho (com th) e linha de filtro (ctl01)
                        tr_html = tr.get_attribute("outerHTML") or ""
                        if "ctl01" in tr_html or "GridView1_ctl01" in tr_html:
                            continue
                            
                        # Verificar se tem células td
                        tds = tr.find_elements(By.TAG_NAME, "td")
                        if len(tds) >= 5:
                            # Verificar se tem conteúdo
                            first_td_text = tds[0].text.strip() if tds[0].text else ""
                            if first_td_text and len(first_td_text) > 2 and "Nenhum" not in first_td_text:
                                data_rows.append(tr)
                    except:
                        continue
                
                if not data_rows:
                    print("Nenhuma linha de dados encontrada após filtro")
                    return None
                
                print(f"Encontradas {len(data_rows)} linha(s) de dados (pode ser o primeiro da lista)")
                row = data_rows[0]

            # Extrair dados da linha selecionada
            cells = row.find_elements(By.TAG_NAME, "td")
            
            if len(cells) < 5:
                print(f"Número insuficiente de células: {len(cells)}")
                return None

            # Extrair dados das células
            name = self._extract_cell_text(cells[0]) if len(cells) > 0 else ""
            birth_date = self._extract_cell_text(cells[1]) if len(cells) > 1 else ""
            responsible1 = self._extract_cell_text(cells[2]) if len(cells) > 2 else ""
            responsible2 = self._extract_cell_text(cells[3]) if len(cells) > 3 else ""
            register_date = self._extract_cell_text(cells[4]) if len(cells) > 4 else ""

            result = {
                "name": name.strip(),
                "birth_date": birth_date.strip(),
                "responsible1": responsible1.strip() if responsible1.strip() else None,
                "responsible2": responsible2.strip() if responsible2.strip() else None,
                "register_date": register_date.strip(),
                "cpf": cpf_value,  # Usa o CPF que foi buscado
            }
            
            print(f"Dados extraídos para CPF {cpf_value}: {result}")
            
            # VERIFICAÇÃO: Confirma se o resultado realmente corresponde ao CPF buscado
            row_text = row.text.lower()
            if cpf_clean not in re.sub(r'\D', '', row_text.lower()):
                print(f"ATENÇÃO: O resultado pode não corresponder ao CPF {cpf_value}")
                print(f"Texto da linha: {row_text[:200]}")
            
            return result

        except Exception as e:
            print(f"Erro ao extrair resultados: {e}")
            return None

    def _extract_cell_text(self, cell):
        """Extrai texto de uma célula, tentando diferentes abordagens."""
        try:
            # Primeiro tenta elementos span internos
            spans = cell.find_elements(By.TAG_NAME, "span")
            for span in spans:
                text = span.text.strip()
                if text:
                    return text
            
            # Tenta links
            links = cell.find_elements(By.TAG_NAME, "a")
            for link in links:
                text = link.text.strip()
                if text:
                    return text
            
            # Retorna o texto direto da célula
            return cell.text.strip()
            
        except Exception as e:
            print(f"Erro ao extrair texto da célula: {e}")
            return cell.text.strip() if hasattr(cell, 'text') else ""

    def _direct_form_submit_with_js(self, cpf_value):
        """Método mais agressivo usando JavaScript para forçar o submit."""
        try:
            print("Tentando submit direto via JavaScript...")
            
            script = """
            // Função para configurar campo
            function setInputValue(inputId, value) {
                var input = document.getElementById(inputId);
                if (input) {
                    input.value = value;
                    // Disparar eventos
                    var events = ['input', 'change', 'keyup', 'blur'];
                    events.forEach(function(eventType) {
                        var event = new Event(eventType, { bubbles: true });
                        input.dispatchEvent(event);
                    });
                    return true;
                }
                return false;
            }
            
            // 1. Limpar campo CPF
            setInputValue('ctl00_ContentPlaceHolder1_GridView1_ctl01_fltCPF', '');
            
            // 2. Preencher com novo valor
            var success = setInputValue('ctl00_ContentPlaceHolder1_GridView1_ctl01_fltCPF', '%s');
            
            if (success) {
                // 3. Encontrar e clicar no botão Filtrar
                var filterBtn = document.getElementById('ctl00_ContentPlaceHolder1_GridView1_ctl01_BtnFiltrar');
                if (filterBtn) {
                    // Simular clique real
                    var mouseEvents = ['mousedown', 'mouseup', 'click'];
                    mouseEvents.forEach(function(eventType) {
                        var event = new MouseEvent(eventType, {
                            view: window,
                            bubbles: true,
                            cancelable: true
                        });
                        filterBtn.dispatchEvent(event);
                    });
                    return 'filter_clicked_with_events';
                } else {
                    // Tentar __doPostBack
                    if (typeof __doPostBack === 'function') {
                        __doPostBack('ctl00$ContentPlaceHolder1$GridView1$ctl01$BtnFiltrar', '');
                        return 'postback_called';
                    }
                    return 'no_filter_button';
                }
            }
            return 'cpf_not_set';
            """ % cpf_value
            
            result = self.browser.driver.execute_script(script)
            print(f"Resultado do submit JS: {result}")
            
            time.sleep(5)
            self._wait_for_ajax(15)
            
            return True
            
        except Exception as e:
            print(f"Erro no submit JS: {e}")
            return False