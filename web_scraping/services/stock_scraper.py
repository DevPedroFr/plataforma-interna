# web_scraping/services/stock_scraper.py (versão aprimorada)
import time
import re
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from django.conf import settings
from .base_scraper import BaseScraper
from core.models import Vaccine

class StockScraper(BaseScraper):
    def __init__(self, browser_manager):
        super().__init__(browser_manager)
        self.stock_url = "https://aruja.gocfranquias.com.br/Cadastro/Vacinas.aspx"
        self.max_pages = getattr(settings, 'STOCK_SCRAPER_MAX_PAGES', 100)
    
    def scrape_stock_data(self):
        """Extrai dados de estoque de todas as páginas"""
        if not self.ensure_login():
            return []
        
        print("🔄 Navegando para página de estoque...")
        self.browser.driver.get(self.stock_url)
        
        # Aguarda a página carregar completamente (tabela ou container)
        try:
            WebDriverWait(self.browser.driver, 20).until(
                EC.any_of(
                    EC.presence_of_element_located((By.ID, "ctl00_ContentPlaceHolder1_GridView1")),
                    EC.presence_of_element_located((By.ID, "ctl00_ContentPlaceHolder1_upgrid")),
                    EC.presence_of_element_located((By.CSS_SELECTOR, "table.GridPrincipal")),
                )
            )
            print("✅ Tabela/Container de estoque carregado")
        except TimeoutException:
            print("❌ Tabela de estoque não encontrada")
            return []
        
        stock_data = []
        page = 1
        
        while page <= self.max_pages:
            print(f"\n📄 Processando página {page}...")
            
            # Extrai dados da página atual
            page_data = self._extract_page_data()
            
            if not page_data:
                print("ℹ️ Nenhum dado encontrado nesta página")
                break
            
            stock_data.extend(page_data)
            print(f"✅ Página {page}: {len(page_data)} itens extraídos (total: {len(stock_data)})")
            
            # Verifica se há próxima página
            if not self._has_next_page():
                print("ℹ️ Última página alcançada")
                break
            
            # Navega para próxima página
            if not self._go_to_next_page():
                print("ℹ️ Não foi possível navegar para próxima página")
                break
            
            page += 1
            
            # Pequena pausa para evitar sobrecarga
            time.sleep(2)
        
        print(f"\n✅ Extração concluída: {len(stock_data)} itens de {page-1} páginas")
        return stock_data
    
    def _extract_page_data(self):
        """Extrai dados da página atual"""
        page_data = []
        
        try:
            # Espera o grid existir; seja tolerante com o seletor
            WebDriverWait(self.browser.driver, 15).until(
                EC.presence_of_element_located((By.ID, "ctl00_ContentPlaceHolder1_GridView1"))
            )

            # Coleta todas as linhas candidatas dentro do grid
            all_rows = self.browser.driver.find_elements(By.CSS_SELECTOR, "#ctl00_ContentPlaceHolder1_GridView1 tr")
            rows = []
            for r in all_rows:
                try:
                    classes = (r.get_attribute("class") or "").lower()
                    # Ignora cabeçalho sticky e linha de paginação
                    if "sticky" in classes or "gridview-pager" in classes or "pagination-container" in classes:
                        continue
                    # Linha de dados deve ter ao menos um TD
                    if r.find_elements(By.TAG_NAME, "td"):
                        rows.append(r)
                except:
                    continue

            print(f"🔍 Encontradas {len(rows)} linhas de dados")

            for i, row in enumerate(rows):
                try:
                    # Pula linhas vazias ou de paginação
                    if not row.text.strip():
                        continue
                    
                    # Extrai dados da linha
                    vaccine_data = self._extract_row_data(row, i)
                    if vaccine_data:
                        page_data.append(vaccine_data)
                        print(f"  ✅ Linha {i+1}: {vaccine_data['name'][:50]}...")
                        
                except Exception as e:
                    print(f"  ❌ Erro na linha {i+1}: {str(e)}")
                    continue
        
        except Exception as e:
            print(f"❌ Erro ao extrair dados da página: {str(e)}")
        
        return page_data
    
    def _extract_row_data(self, row, index):
        """Extrai dados de uma linha específica"""
        try:
            # Encontra todas as células da linha
            cells = row.find_elements(By.TAG_NAME, "td")

            if len(cells) < 1:
                return None

            # 1. Nome da vacina (tenta spans Label1, senão texto do primeiro TD)
            def _safe_text(cell, selector_list):
                for sel in selector_list:
                    try:
                        el = cell.find_element(By.CSS_SELECTOR, sel)
                        txt = el.text.strip()
                        if txt:
                            return txt
                    except:
                        continue
                return cell.text.strip()

            name = _safe_text(cells[0], ["span[id*='Label1']", "span"]) or ""

            # 2. Laboratório: segunda coluna quando existir
            laboratory = _safe_text(cells[1], ["span[id*='Label2']", "span"]) if len(cells) > 1 else ""

            # 3/4. Preços: busca padrão monetário em qualquer TD
            sale_price = 0.0
            purchase_price = 0.0
            for c in cells:
                txt = c.text.strip()
                if not txt:
                    continue
                # Prioriza primeiro preço encontrado como venda
                if sale_price == 0.0:
                    maybe = self._parse_price(txt)
                    if maybe > 0.0:
                        sale_price = maybe
                        continue
                # Se já há venda, tenta compra
                if purchase_price == 0.0:
                    maybe2 = self._parse_price(txt)
                    if maybe2 > 0.0 and maybe2 != sale_price:
                        purchase_price = maybe2

            # 5+. Quantidades: coleta todos os inteiros visíveis
            quantities = []
            for c in cells:
                q = self._parse_quantity(c.text)
                if q is not None and isinstance(q, int):
                    # aceita números positivos
                    if q >= 0 and (str(q) in (c.text or "")):
                        quantities.append(q)

            # Heurística: se houver ao menos 1 número, assume disponível = primeiro,
            # atual = segundo (se existir) e mínimo = último (se houver mais de 2)
            available_stock = quantities[0] if len(quantities) >= 1 else 0
            current_stock = quantities[1] if len(quantities) >= 2 else available_stock
            min_stock = quantities[-1] if len(quantities) >= 3 else 0

            # Idades (caso existam): tenta nas últimas colunas
            min_age = _safe_text(cells[-2], ["span"]) if len(cells) >= 2 else ""
            max_age = _safe_text(cells[-1], ["span"]) if len(cells) >= 1 else ""
            
            # Se o nome estiver vazio, pula a linha
            if not name or name == "Nome não encontrado":
                return None
            
            vaccine_data = {
                'name': name,
                'laboratory': laboratory,
                'purchase_price': purchase_price,
                'sale_price': sale_price,
                'current_stock': current_stock,
                'available_stock': available_stock,
                'min_stock': min_stock,
                'minimum_stock': min_stock,  # Campo duplicado para compatibilidade
                'min_age': min_age,
                'max_age': max_age,
            }
            
            return vaccine_data
            
        except Exception as e:
            print(f"  ❌ Erro ao processar linha {index+1}: {str(e)}")
            return None
    
    def _extract_cell_text(self, cell):
        """Extrai texto de uma célula, priorizando spans"""
        try:
            # Tenta encontrar span dentro da célula
            spans = cell.find_elements(By.TAG_NAME, "span")
            if spans:
                # Pega o último span (que geralmente contém o dado real)
                return spans[-1].text.strip()
            
            # Se não tem span, usa o texto da célula
            return cell.text.strip()
            
        except:
            return ""
    
    def _has_next_page(self):
        """Verifica se existe próxima página"""
        try:
            pager = None
            # tenta localizar a linha de paginação do GridView
            for el in self.browser.driver.find_elements(By.CSS_SELECTOR, "#ctl00_ContentPlaceHolder1_GridView1 tr"):
                classes = (el.get_attribute("class") or "").lower()
                if "gridview-pager" in classes or "pagination-container" in classes:
                    pager = el
                    break

            scope = pager if pager else self.browser.driver
            links = scope.find_elements(
                By.XPATH,
                "//a[contains(@href, 'Page$Next') or contains(@onclick, 'Page$Next') or contains(@href, 'Page%24Next')]"
            )
            return len(links) > 0
        except Exception as e:
            print(f"⚠️ Erro ao verificar próxima página: {str(e)}")
            return False
    
    def _go_to_next_page(self):
        """Navega para próxima página usando __doPostBack"""
        try:
            # Método 1: usar __doPostBack direto no GridView
            if self._try_postback_next():
                return True

            # Método 2: clicar nos links de paginação 'Next'
            if self._find_and_click_pagination():
                return True

            # Método 3: clicar no botão de próxima imagem, se existir
            if self._click_next_button():
                return True

            return False
        except Exception as e:
            print(f"❌ Erro ao navegar para próxima página: {str(e)}")
            return False
    
    def _try_postback_next(self):
        """Tenta navegar usando __doPostBack"""
        try:
            script = """
            if (typeof __doPostBack === 'function') {
                __doPostBack('ctl00$ContentPlaceHolder1$GridView1', 'Page$Next');
                return true;
            }
            return false;
            """
            result = self.browser.driver.execute_script(script)
            if result:
                print("🔀 Navegando via __doPostBack...")
                # Aguarda atualização da página
                time.sleep(getattr(settings, 'STOCK_SCRAPER_AJAX_WAIT_SECONDS', 2.0))
                WebDriverWait(self.browser.driver, 15).until(
                    EC.presence_of_element_located((By.ID, "ctl00_ContentPlaceHolder1_GridView1"))
                )
                return True
                
        except Exception as e:
            print(f"⚠️ __doPostBack falhou: {str(e)}")
        
        return False
    
    def _click_next_button(self):
        """Tenta clicar no botão de próxima página"""
        try:
            # Procura botão de próxima página
            next_btn = self.browser.driver.find_element(
                By.CSS_SELECTOR,
                "input[src*='resultset_next.png'][onclick*='Page$Next'], " +
                "img[src*='resultset_next.png'][onclick*='Page$Next']"
            )
            
            # Rola até o botão
            self.browser.driver.execute_script("arguments[0].scrollIntoView();", next_btn)
            time.sleep(0.5)
            
            # Clica no botão
            next_btn.click()
            print("🔀 Clicando no botão 'Próxima'...")
            
            # Aguarda atualização
            time.sleep(getattr(settings, 'STOCK_SCRAPER_AJAX_WAIT_SECONDS', 2.0))
            WebDriverWait(self.browser.driver, 15).until(
                EC.presence_of_element_located((By.ID, "ctl00_ContentPlaceHolder1_GridView1"))
            )
            
            return True
            
        except NoSuchElementException:
            print("⚠️ Botão 'Próxima' não encontrado")
            return False
        except Exception as e:
            print(f"⚠️ Erro ao clicar no botão: {str(e)}")
            return False
    
    def _find_and_click_pagination(self):
        """Encontra e clica em link de paginação"""
        try:
            # Procura por links de paginação
            links = self.browser.driver.find_elements(
                By.XPATH,
                "//a[contains(@href, 'javascript:__doPostBack') and " +
                "(contains(@href, 'Page$Next') or contains(@href, 'Page%24Next'))]"
            )
            
            for link in links:
                try:
                    href = link.get_attribute('href') or ''
                    onclick = link.get_attribute('onclick') or ''
                    
                    if 'Page$Next' in href or 'Page$Next' in onclick or 'Page%24Next' in href:
                        self.browser.driver.execute_script("arguments[0].scrollIntoView();", link)
                        time.sleep(0.5)
                        link.click()
                        print("🔀 Clicando em link de paginação...")
                        
                        # Aguarda atualização
                        time.sleep(getattr(settings, 'STOCK_SCRAPER_AJAX_WAIT_SECONDS', 2.0))
                        WebDriverWait(self.browser.driver, 15).until(
                            EC.presence_of_element_located((By.ID, "ctl00_ContentPlaceHolder1_GridView1"))
                        )
                        
                        return True
                except:
                    continue
            
            return False
            
        except Exception as e:
            print(f"⚠️ Erro ao buscar paginação: {str(e)}")
            return False
    
    def _parse_price(self, price_text):
        """Converte texto de preço para float"""
        try:
            if not price_text or price_text.strip() == '':
                return 0.0
            
            # Remove R$, espaços e pontos de milhar
            text = price_text.strip()
            text = text.replace('R$', '').replace(' ', '')
            
            # Substitui vírgula por ponto para decimal
            if ',' in text and '.' in text:
                # Formato brasileiro: 1.234,56 -> 1234.56
                text = text.replace('.', '').replace(',', '.')
            elif ',' in text:
                # Apenas vírgula decimal
                text = text.replace(',', '.')
            
            # Remove qualquer caractere não numérico exceto ponto
            text = re.sub(r'[^\d\.]', '', text)
            
            return float(text) if text else 0.0
            
        except Exception as e:
            print(f"⚠️ Erro ao converter preço '{price_text}': {str(e)}")
            return 0.0
    
    def _parse_quantity(self, quantity_text):
        """Converte texto de quantidade para inteiro"""
        try:
            if not quantity_text or quantity_text.strip() == '':
                return 0
            
            # Remove todos os caracteres não numéricos
            text = re.sub(r'[^\d]', '', quantity_text.strip())
            
            return int(text) if text else 0
            
        except Exception as e:
            print(f"⚠️ Erro ao converter quantidade '{quantity_text}': {str(e)}")
            return 0
    
    def sync_stock_to_database(self):
        """Sincroniza dados de estoque com o banco de dados"""
        print("🔄 Iniciando sincronização completa de estoque...")
        
        try:
            # Extrai dados de todas as páginas
            stock_data = self.scrape_stock_data()
            
            if not stock_data:
                return {
                    'status': 'error',
                    'message': 'Nenhum dado foi extraído',
                    'total_scraped': 0,
                    'created': 0,
                    'updated': 0,
                    'errors': []
                }
            
            updated_count = 0
            created_count = 0
            errors = []
            
            print(f"💾 Salvando {len(stock_data)} itens no banco de dados...")
            
            for i, vaccine_data in enumerate(stock_data):
                try:
                    # Busca ou cria vacina
                    vaccine, created = Vaccine.objects.get_or_create(
                        name=vaccine_data['name'],
                        defaults={
                            'laboratory': vaccine_data.get('laboratory', ''),
                            'current_stock': vaccine_data.get('current_stock', 0),
                            'available_stock': vaccine_data.get('available_stock', 0),
                            'min_stock': vaccine_data.get('min_stock', 0),
                            'minimum_stock': vaccine_data.get('min_stock', 0),
                            'purchase_price': vaccine_data.get('purchase_price', 0.0),
                            'sale_price': vaccine_data.get('sale_price', 0.0),
                        }
                    )
                    
                    if not created:
                        # Atualiza vacina existente
                        vaccine.laboratory = vaccine_data.get('laboratory', vaccine.laboratory)
                        vaccine.current_stock = vaccine_data.get('current_stock', vaccine.current_stock)
                        vaccine.available_stock = vaccine_data.get('available_stock', vaccine.available_stock)
                        vaccine.min_stock = vaccine_data.get('min_stock', vaccine.min_stock)
                        vaccine.minimum_stock = vaccine_data.get('min_stock', vaccine.minimum_stock)
                        
                        if vaccine_data.get('purchase_price', 0.0) > 0:
                            vaccine.purchase_price = vaccine_data['purchase_price']
                        if vaccine_data.get('sale_price', 0.0) > 0:
                            vaccine.sale_price = vaccine_data['sale_price']
                    
                    vaccine.save()
                    
                    if created:
                        created_count += 1
                    else:
                        updated_count += 1
                        
                    if (i + 1) % 10 == 0:
                        print(f"  📊 Progresso: {i+1}/{len(stock_data)}")
                        
                except Exception as e:
                    error_msg = f"Erro ao salvar '{vaccine_data.get('name', 'Desconhecido')}': {str(e)}"
                    errors.append(error_msg)
                    print(f"  ❌ {error_msg}")
            
            result = {
                'status': 'success',
                'message': f"Sincronização concluída! {created_count} criadas, {updated_count} atualizadas",
                'total_scraped': len(stock_data),
                'created': created_count,
                'updated': updated_count,
                'errors': errors,
            }
            
            print(f"\n✅ {result['message']}")
            return result
            
        except Exception as e:
            error_msg = f"Erro na sincronização: {str(e)}"
            print(f"❌ {error_msg}")
            return {
                'status': 'error',
                'message': error_msg,
                'total_scraped': 0,
                'created': 0,
                'updated': 0,
                'errors': [error_msg]
            }