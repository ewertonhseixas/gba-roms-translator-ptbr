/**
 * GBA Pixel Studio - Interactive Pixel Art & Text-in-Tiles Editor
 * Engine de edição pixel art e hardware specs GBA
 */

class GBAEditor {
    constructor() {
        // Estado
        this.game = "sn1";
        this.catalog = [];
        this.currentAsset = null;
        this.width = 160;
        this.height = 22;
        this.pixels = [];      // 1D array de índices da paleta (length = width * height)
        this.origPixels = [];  // Cópia original da ROM
        this.palette = [];     // [[r, g, b], ...]
        this.primaryColor = 1;
        this.secondaryColor = 0;

        // Ferramentas & Visualização
        this.tool = "pencil";  // pencil, eraser, picker, bucket, line, rect, rect-fill, select, stamp
        this.brushSize = 1;
        this.zoom = 16;
        this.panX = 0;
        this.panY = 0;
        this.isDrawing = false;
        this.isPanning = false;
        this.drawMouseButton = 0; // 0 = primária, 2 = secundária
        this.dragStart = { x: 0, y: 0 };
        this.currentMousePos = { x: -1, y: -1 };

        // Overlays
        this.showTileGrid = true;
        this.showPixelGrid = true;
        this.onionSkinOpacity = 0.35;
        this.peekOriginal = false;

        // Histórico
        this.undoStack = [];
        this.redoStack = [];
        this.maxUndo = 35;

        // Seleção & Text Stamper
        this.selection = null; // { x, y, w, h, pixels, floating: bool }
        this.textStamp = null; // { text, font, width, height, grid }
        this.mockupScale = 1;
        this.mockupBg = "#000000";

        // Elementos DOM
        this.initDOM();
        this.initEvents();
        this.loadCatalog();
    }

    initDOM() {
        this.dom = {
            viewport: document.getElementById("viewport"),
            canvasWrapper: document.getElementById("canvasWrapper"),
            canvasBase: document.getElementById("canvasBase"),
            canvasMain: document.getElementById("canvasMain"),
            canvasOverlay: document.getElementById("canvasOverlay"),
            mockupCanvas: document.getElementById("mockupCanvas"),

            // Contextos 2D
            ctxBase: document.getElementById("canvasBase").getContext("2d"),
            ctxMain: document.getElementById("canvasMain").getContext("2d"),
            ctxOverlay: document.getElementById("canvasOverlay").getContext("2d"),
            ctxMockup: document.getElementById("mockupCanvas").getContext("2d"),

            // Headers & Badges
            gameSelect: document.getElementById("gameSelect"),
            activeAssetTitle: document.getElementById("activeAssetTitle"),
            activeAssetStatus: document.getElementById("activeAssetStatus"),
            prevBtn: document.getElementById("prevBtn"),
            nextBtn: document.getElementById("nextBtn"),
            saveBtn: document.getElementById("saveBtn"),
            downloadBtn: document.getElementById("downloadBtn"),

            // Sidebars
            assetList: document.getElementById("assetList"),
            searchInput: document.getElementById("searchInput"),
            tabButtons: document.querySelectorAll(".sidebar-tab-btn"),
            paletteGrid: document.getElementById("paletteGrid"),
            primaryColorChip: document.getElementById("primaryColorChip"),
            secondaryColorChip: document.getElementById("secondaryColorChip"),
            primaryHex: document.getElementById("primaryHex"),
            secondaryHex: document.getElementById("secondaryHex"),

            // Status bar
            statusCoords: document.getElementById("statusCoords"),
            statusTile: document.getElementById("statusTile"),
            statusColor: document.getElementById("statusColor"),
            statusZoom: document.getElementById("statusZoom"),
            statusDims: document.getElementById("statusDims"),

            // Context card
            contextOrigText: document.getElementById("contextOrigText"),
            contextSuggText: document.getElementById("contextSuggText"),
            contextLocation: document.getElementById("contextLocation"),
            contextTargetPath: document.getElementById("contextTargetPath"),

            // Tool buttons
            toolBtns: document.querySelectorAll("[data-tool]"),
            brushSizeSelect: document.getElementById("brushSizeSelect"),
            tileGridBtn: document.getElementById("tileGridBtn"),
            pixelGridBtn: document.getElementById("pixelGridBtn"),
            onionSlider: document.getElementById("onionSlider"),
            zoomInBtn: document.getElementById("zoomInBtn"),
            zoomOutBtn: document.getElementById("zoomOutBtn"),
            zoomResetBtn: document.getElementById("zoomResetBtn"),
            undoBtn: document.getElementById("undoBtn"),
            redoBtn: document.getElementById("redoBtn"),
            revertBtn: document.getElementById("revertBtn"),
            clearBtn: document.getElementById("clearBtn"),

            // Modais
            textStampModal: document.getElementById("textStampModal"),
            textStampInput: document.getElementById("textStampInput"),
            textStampFontSelect: document.getElementById("textStampFontSelect"),
            textStampShadowCheck: document.getElementById("textStampShadowCheck"),
            textStampApplyBtn: document.getElementById("textStampApplyBtn"),
            textStampCloseBtn: document.getElementById("textStampCloseBtn"),
            shortcutsModal: document.getElementById("shortcutsModal"),
            shortcutsBtn: document.getElementById("shortcutsBtn"),
            shortcutsCloseBtn: document.getElementById("shortcutsCloseBtn"),

            // Mockup Controls
            scaleBtns: document.querySelectorAll("[data-mockup-scale]"),
            mockupBgSelect: document.getElementById("mockupBgSelect"),
            toastContainer: document.getElementById("toastContainer"),
        };
    }

    initEvents() {
        // Seleção de jogo
        this.dom.gameSelect.addEventListener("change", (e) => {
            this.game = e.target.value;
            this.loadCatalog();
        });

        // Navegação de imagens
        this.dom.prevBtn.addEventListener("click", () => this.navigateCatalog(-1));
        this.dom.nextBtn.addEventListener("click", () => this.navigateCatalog(1));

        // Busca no catálogo
        this.dom.searchInput.addEventListener("input", (e) => this.filterCatalog(e.target.value));

        // Abas da barra lateral
        this.dom.tabButtons.forEach(btn => {
            btn.addEventListener("click", () => {
                this.dom.tabButtons.forEach(b => b.classList.remove("active"));
                btn.classList.add("active");
                const tab = btn.dataset.tab;
                if (tab === "catalog") {
                    this.renderCatalogList();
                } else if (tab === "all") {
                    this.loadAllExtracted();
                }
            });
        });

        // Botões de Ferramentas
        this.dom.toolBtns.forEach(btn => {
            btn.addEventListener("click", () => {
                this.setTool(btn.dataset.tool);
            });
        });

        // Tamanho do pincel
        if (this.dom.brushSizeSelect) {
            this.dom.brushSizeSelect.addEventListener("change", (e) => {
                this.brushSize = parseInt(e.target.value, 10) || 1;
            });
        }

        // Grids & Onion Skin
        this.dom.tileGridBtn.addEventListener("click", () => {
            this.showTileGrid = !this.showTileGrid;
            this.dom.tileGridBtn.classList.toggle("active", this.showTileGrid);
            this.renderOverlay();
        });

        this.dom.pixelGridBtn.addEventListener("click", () => {
            this.showPixelGrid = !this.showPixelGrid;
            this.dom.pixelGridBtn.classList.toggle("active", this.showPixelGrid);
            this.renderOverlay();
        });

        this.dom.onionSlider.addEventListener("input", (e) => {
            this.onionSkinOpacity = parseFloat(e.target.value);
            this.renderBase();
        });

        // Zoom & Pan
        this.dom.zoomInBtn.addEventListener("click", () => this.setZoom(this.zoom * 1.5));
        this.dom.zoomOutBtn.addEventListener("click", () => this.setZoom(this.zoom / 1.5));
        this.dom.zoomResetBtn.addEventListener("click", () => this.resetView());

        // Ações de Canvas
        this.dom.saveBtn.addEventListener("click", () => this.saveToProject());
        this.dom.downloadBtn.addEventListener("click", () => this.downloadPNG());
        this.dom.undoBtn.addEventListener("click", () => this.undo());
        this.dom.redoBtn.addEventListener("click", () => this.redo());
        this.dom.revertBtn.addEventListener("click", () => this.revertToOriginal());
        this.dom.clearBtn.addEventListener("click", () => this.clearCanvas());

        // Modais
        this.dom.textStampApplyBtn.addEventListener("click", () => this.prepareTextStamp());
        this.dom.textStampCloseBtn.addEventListener("click", () => this.closeTextStampModal());
        this.dom.shortcutsBtn.addEventListener("click", () => this.dom.shortcutsModal.classList.add("active"));
        this.dom.shortcutsCloseBtn.addEventListener("click", () => this.dom.shortcutsModal.classList.remove("active"));

        // Mockup controls
        this.dom.scaleBtns.forEach(btn => {
            btn.addEventListener("click", () => {
                this.dom.scaleBtns.forEach(b => b.classList.remove("active"));
                btn.classList.add("active");
                this.mockupScale = parseInt(btn.dataset.mockupScale, 10);
                this.renderMockup();
            });
        });
        if (this.dom.mockupBgSelect) {
            this.dom.mockupBgSelect.addEventListener("change", (e) => {
                this.mockupBg = e.target.value;
                document.querySelector(".mockup-box").style.backgroundColor = this.mockupBg;
            });
        }

        // Viewport Mouse Events (Canvas Interaction)
        this.dom.viewport.addEventListener("mousedown", (e) => this.onMouseDown(e));
        window.addEventListener("mousemove", (e) => this.onMouseMove(e));
        window.addEventListener("mouseup", (e) => this.onMouseUp(e));
        this.dom.viewport.addEventListener("wheel", (e) => this.onWheel(e), { passive: false });
        this.dom.viewport.addEventListener("contextmenu", (e) => e.preventDefault());

        // Teclado (Atalhos)
        window.addEventListener("keydown", (e) => this.onKeyDown(e));
        window.addEventListener("keyup", (e) => this.onKeyUp(e));
    }

    /* ----------------------------------------------------
       Carregamento de Dados & Catálogo
       ---------------------------------------------------- */
    async loadCatalog() {
        try {
            const res = await fetch(`/api/catalog?game=${this.game}`);
            const data = await res.json();
            this.catalog = data.items || [];
            this.renderCatalogList();

            // Carrega o primeiro item por padrão
            if (this.catalog.length > 0) {
                this.loadAsset(this.catalog[0]);
            }
        } catch (err) {
            this.showToast("Erro ao carregar catálogo: " + err.message, "error");
        }
    }

    renderCatalogList() {
        this.dom.assetList.innerHTML = "";
        if (this.catalog.length === 0) {
            this.dom.assetList.innerHTML = `<div style="padding:16px;color:var(--text-muted);text-align:center;">Nenhuma imagem catalogada encontrada.</div>`;
            return;
        }

        this.catalog.forEach((item, index) => {
            const card = document.createElement("div");
            card.className = "asset-card" + (this.currentAsset && this.currentAsset.id === item.id ? " active" : "");

            const isDone = item.status && item.status.includes("✅");
            const statusClass = isDone ? "status-done" : "status-pending";

            card.innerHTML = `
                <div class="asset-card-top">
                    <span class="asset-card-id">${item.id}</span>
                    <span class="asset-status-pill ${statusClass}">${item.status || "⏳ Pendente"}</span>
                </div>
                <div class="asset-card-filename" title="${item.filename}">${item.filename}</div>
                <div class="asset-card-text">
                    ${item.orig_text ? `Orig: <em>${item.orig_text}</em>` : ""}
                    ${item.sugg_text ? `<br>PT: <strong>${item.sugg_text}</strong>` : ""}
                </div>
                <div class="asset-card-dims">${item.dims || `${item.width}x${item.height}`} • ${item.format || "4bpp"}</div>
            `;

            card.addEventListener("click", () => this.loadAsset(item));
            this.dom.assetList.appendChild(card);
        });
    }

    filterCatalog(query) {
        const q = query.toLowerCase();
        const cards = this.dom.assetList.querySelectorAll(".asset-card");
        this.catalog.forEach((item, index) => {
            const match = !q ||
                item.id.toLowerCase().includes(q) ||
                item.filename.toLowerCase().includes(q) ||
                (item.orig_text && item.orig_text.toLowerCase().includes(q)) ||
                (item.sugg_text && item.sugg_text.toLowerCase().includes(q));
            if (cards[index]) {
                cards[index].style.display = match ? "flex" : "none";
            }
        });
    }

    async loadAllExtracted() {
        this.dom.assetList.innerHTML = `<div style="padding:16px;color:var(--text-muted);text-align:center;">Carregando todas as imagens extraídas...</div>`;
        try {
            const res = await fetch(`/api/search_extracted?game=${this.game}`);
            const data = await res.json();
            this.dom.assetList.innerHTML = "";
            (data.results || []).forEach(file => {
                const card = document.createElement("div");
                card.className = "asset-card";
                card.innerHTML = `
                    <div class="asset-card-id">${file.name}</div>
                    <div class="asset-card-filename">${file.rel_path}</div>
                `;
                card.addEventListener("click", () => {
                    this.loadAsset({
                        id: file.name,
                        filename: file.rel_path,
                        location: "Archive Extracted",
                        dims: "",
                        orig_text: "",
                        sugg_text: "",
                        status: "Extraído"
                    });
                });
                this.dom.assetList.appendChild(card);
            });
        } catch (err) {
            this.showToast("Erro ao carregar arquivos extraídos: " + err.message, "error");
        }
    }

    async loadAsset(asset) {
        this.currentAsset = asset;

        // Atualiza estilo ativo na lista
        const cards = this.dom.assetList.querySelectorAll(".asset-card");
        cards.forEach(c => c.classList.remove("active"));
        const activeCard = Array.from(cards).find(c => c.querySelector(".asset-card-id")?.textContent === asset.id);
        if (activeCard) activeCard.classList.add("active");

        // Atualiza header & context
        this.dom.activeAssetTitle.textContent = `${asset.id} - ${asset.filename}`;
        this.dom.activeAssetStatus.textContent = asset.status || "⏳ Pendente";
        this.dom.activeAssetStatus.className = "asset-status-pill " + (asset.status && asset.status.includes("✅") ? "status-done" : "status-pending");

        this.dom.contextOrigText.textContent = asset.orig_text || "N/A";
        this.dom.contextSuggText.textContent = asset.sugg_text || "N/A";
        this.dom.contextLocation.textContent = asset.location || "N/A";
        this.dom.contextTargetPath.textContent = asset.filename;

        // Busca dados no backend
        try {
            const url = `/api/image_data?game=${this.game}&path=${encodeURIComponent(asset.filename)}&id=${encodeURIComponent(asset.id)}`;
            const res = await fetch(url);
            if (!res.ok) {
                const err = await res.json();
                throw new Error(err.error || "Falha ao carregar imagem");
            }
            const data = await res.json();

            this.width = data.width;
            this.height = data.height;
            this.palette = data.palette;
            this.origPalette = data.orig_palette || data.palette;
            this.pixels = [...data.pixels];
            this.origPixels = [...data.orig_pixels];
            this.relPath = data.rel_path || asset.filename;

            // Reseta histórico
            this.undoStack = [];
            this.redoStack = [];
            this.selection = null;

            // Configura telas
            this.setupCanvases();
            this.renderPalette();
            this.renderBase();
            this.renderMain();
            this.renderOverlay();
            this.renderMockup();
            this.resetView();

            this.dom.statusDims.textContent = `${this.width}x${this.height} px (${Math.ceil(this.width/8)}x${Math.ceil(this.height/8)} tiles)`;
            this.showToast(`Carregado: ${asset.id} (${this.width}x${this.height} px)`);
        } catch (err) {
            this.showToast("Erro ao abrir imagem: " + err.message, "error");
        }
    }

    navigateCatalog(delta) {
        if (!this.catalog.length || !this.currentAsset) return;
        const curIdx = this.catalog.findIndex(it => it.id === this.currentAsset.id);
        if (curIdx === -1) return;
        const nextIdx = (curIdx + delta + this.catalog.length) % this.catalog.length;
        this.loadAsset(this.catalog[nextIdx]);
    }

    /* ----------------------------------------------------
       Canvas & Camadas
       ---------------------------------------------------- */
    setupCanvases() {
        const w = this.width;
        const h = this.height;

        [this.dom.canvasBase, this.dom.canvasMain, this.dom.canvasOverlay].forEach(c => {
            c.width = w;
            c.height = h;
            c.style.width = `${w}px`;
            c.style.height = `${h}px`;
        });

        this.dom.canvasWrapper.style.width = `${w}px`;
        this.dom.canvasWrapper.style.height = `${h}px`;

        // Desativa interpolação para nitidez pixel art
        [this.dom.ctxBase, this.dom.ctxMain, this.dom.ctxOverlay, this.dom.ctxMockup].forEach(ctx => {
            ctx.imageSmoothingEnabled = false;
        });
    }

    resetView() {
        // Encontra zoom ideal para preencher 70% da viewport
        const rect = this.dom.viewport.getBoundingClientRect();
        const maxW = rect.width * 0.75;
        const maxH = rect.height * 0.75;
        const fitZoom = Math.max(2, Math.min(32, Math.floor(Math.min(maxW / this.width, maxH / this.height))));

        this.zoom = fitZoom;
        this.panX = Math.round((rect.width - this.width * this.zoom) / 2);
        this.panY = Math.round((rect.height - this.height * this.zoom) / 2);
        this.updateViewportTransform();
        this.dom.statusZoom.textContent = `${Math.round(this.zoom * 100)}%`;
    }

    setZoom(newZoom, mouseX, mouseY) {
        const prevZoom = this.zoom;
        const clampedZoom = Math.max(1, Math.min(32, Math.round(newZoom)));
        if (clampedZoom === prevZoom) return;

        if (mouseX !== undefined && mouseY !== undefined) {
            // Zoom centralizado sob a posição do mouse
            const rect = this.dom.viewport.getBoundingClientRect();
            const relX = mouseX - rect.left;
            const relY = mouseY - rect.top;

            const canvasX = (relX - this.panX) / prevZoom;
            const canvasY = (relY - this.panY) / prevZoom;

            this.panX = relX - canvasX * clampedZoom;
            this.panY = relY - canvasY * clampedZoom;
        }

        this.zoom = clampedZoom;
        this.updateViewportTransform();
        this.dom.statusZoom.textContent = `${Math.round(this.zoom * 100)}%`;
        this.renderOverlay();
    }

    updateViewportTransform() {
        this.dom.canvasWrapper.style.transform = `translate(${this.panX}px, ${this.panY}px) scale(${this.zoom})`;
    }

    /* ----------------------------------------------------
       Renderização Pixel Art
       ---------------------------------------------------- */
    renderBase() {
        // Camada Base: Referência Original / Onion Skin
        const ctx = this.dom.ctxBase;
        ctx.clearRect(0, 0, this.width, this.height);

        const opacity = this.peekOriginal ? 1.0 : this.onionSkinOpacity;
        if (opacity <= 0.01) return;

        const imgData = ctx.createImageData(this.width, this.height);
        const d = imgData.data;

        for (let i = 0; i < this.origPixels.length; i++) {
            const palIdx = this.origPixels[i];
            const pOff = i * 4;
            if (palIdx === 0) {
                // Índice 0 transparente
                d[pOff + 3] = 0;
            } else {
                const color = (this.origPalette && this.origPalette[palIdx]) || this.palette[palIdx] || [255, 255, 255];
                d[pOff] = color[0];
                d[pOff + 1] = color[1];
                d[pOff + 2] = color[2];
                d[pOff + 3] = Math.round(255 * opacity);
            }
        }
        ctx.putImageData(imgData, 0, 0);
    }

    renderMain() {
        // Camada Principal: Pixels editados pelo usuário
        const ctx = this.dom.ctxMain;
        ctx.clearRect(0, 0, this.width, this.height);

        if (this.peekOriginal) return; // Se estiver espiando original, oculta edição

        const imgData = ctx.createImageData(this.width, this.height);
        const d = imgData.data;

        for (let i = 0; i < this.pixels.length; i++) {
            const palIdx = this.pixels[i];
            const pOff = i * 4;
            if (palIdx === 0) {
                // Índice 0 é transparente no hardware do GBA
                d[pOff + 3] = 0;
            } else {
                const color = this.palette[palIdx] || [255, 255, 255];
                d[pOff] = color[0];
                d[pOff + 1] = color[1];
                d[pOff + 2] = color[2];
                d[pOff + 3] = 255;
            }
        }
        ctx.putImageData(imgData, 0, 0);
        this.renderMockup();
    }

    renderOverlay() {
        // Camada Superior: Grids, Tile boundaries, seleções e previews
        const ctx = this.dom.ctxOverlay;
        ctx.clearRect(0, 0, this.width, this.height);

        // 1. Grid de 1px (quando zoom >= 6)
        if (this.showPixelGrid && this.zoom >= 6) {
            ctx.strokeStyle = "rgba(255, 255, 255, 0.08)";
            ctx.lineWidth = 1 / this.zoom;

            ctx.beginPath();
            for (let x = 0; x <= this.width; x++) {
                ctx.moveTo(x, 0);
                ctx.lineTo(x, this.height);
            }
            for (let y = 0; y <= this.height; y++) {
                ctx.moveTo(0, y);
                ctx.lineTo(this.width, y);
            }
            ctx.stroke();
        }

        // 2. Grid de Tiles 8x8 do GBA (Inviolável para ROM Hacking)
        if (this.showTileGrid) {
            ctx.strokeStyle = "rgba(245, 158, 11, 0.65)";
            ctx.lineWidth = 1 / this.zoom;

            ctx.beginPath();
            for (let x = 0; x <= this.width; x += 8) {
                ctx.moveTo(x, 0);
                ctx.lineTo(x, this.height);
            }
            for (let y = 0; y <= this.height; y += 8) {
                ctx.moveTo(0, y);
                ctx.lineTo(this.width, y);
            }
            ctx.stroke();
        }

        // 3. Ferramenta de Seleção / Marquee
        if (this.selection) {
            ctx.strokeStyle = "#38bdf8";
            ctx.lineWidth = 1 / this.zoom;
            ctx.setLineDash([2 / this.zoom, 2 / this.zoom]);
            ctx.strokeRect(this.selection.x, this.selection.y, this.selection.w, this.selection.h);
            ctx.setLineDash([]);
        }

        // 4. Ghost do Carimbador de Texto (Cursor Preview)
        if (this.tool === "stamp" && this.textStamp && this.currentMousePos.x >= 0) {
            const sx = this.currentMousePos.x;
            const sy = this.currentMousePos.y;
            const tw = this.textStamp.width;
            const th = this.textStamp.height;

            for (let y = 0; y < th; y++) {
                for (let x = 0; x < tw; x++) {
                    const cIdx = this.textStamp.grid[y][x];
                    if (cIdx >= 0) {
                        const px = sx + x;
                        const py = sy + y;
                        if (px >= 0 && px < this.width && py >= 0 && py < this.height) {
                            const rgb = this.palette[cIdx] || [255, 255, 255];
                            ctx.fillStyle = `rgba(${rgb[0]}, ${rgb[1]}, ${rgb[2]}, 0.75)`;
                            ctx.fillRect(px, py, 1, 1);
                        }
                    }
                }
            }
            ctx.strokeStyle = "#60a5fa";
            ctx.lineWidth = 1 / this.zoom;
            ctx.strokeRect(sx, sy, tw, th);
        }
    }

    renderMockup() {
        // Pré-visualização 1:1 real em tempo de execução
        const cvs = this.dom.mockupCanvas;
        const ctx = this.dom.ctxMockup;
        const scale = this.mockupScale;

        cvs.width = this.width * scale;
        cvs.height = this.height * scale;

        ctx.clearRect(0, 0, cvs.width, cvs.height);
        ctx.imageSmoothingEnabled = false;

        // Renderiza imagem editada
        ctx.drawImage(this.dom.canvasMain, 0, 0, cvs.width, cvs.height);
    }

    /* ----------------------------------------------------
       Paleta de Cores do GBA
       ---------------------------------------------------- */
    renderPalette() {
        const grid = this.dom.paletteGrid;
        grid.innerHTML = "";

        this.palette.forEach((color, index) => {
            const swatch = document.createElement("div");
            swatch.className = "palette-swatch";
            if (index === this.primaryColor) swatch.classList.add("selected-primary");
            if (index === this.secondaryColor) swatch.classList.add("selected-secondary");

            const isIndexZero = (index === 0);
            if (isIndexZero) {
                swatch.style.backgroundImage = "repeating-linear-gradient(45deg, #ef4444 0, #ef4444 4px, transparent 0, transparent 8px)";
                swatch.title = "Índice 0: Transparência PPU (Hardware GBA)";
            } else {
                const hex = this.rgbToHex(color[0], color[1], color[2]);
                swatch.style.backgroundColor = hex;
                swatch.title = `[${index}] ${hex}`;
            }

            swatch.innerHTML = `<span class="swatch-index">${index}</span>`;

            // Botão Esquerdo: Cor Primária | Botão Direito: Cor Secundária
            swatch.addEventListener("click", () => this.selectColor(index, true));
            swatch.addEventListener("contextmenu", (e) => {
                e.preventDefault();
                this.selectColor(index, false);
            });

            grid.appendChild(swatch);
        });

        this.updateColorChips();
    }

    selectColor(index, isPrimary = true) {
        if (index < 0 || index >= this.palette.length) return;
        if (isPrimary) {
            this.primaryColor = index;
        } else {
            this.secondaryColor = index;
        }
        this.renderPalette();
    }

    updateColorChips() {
        const pColor = this.palette[this.primaryColor] || [0, 0, 0];
        const sColor = this.palette[this.secondaryColor] || [0, 0, 0];

        const pHex = this.primaryColor === 0 ? "TRANSP" : this.rgbToHex(pColor[0], pColor[1], pColor[2]);
        const sHex = this.secondaryColor === 0 ? "TRANSP" : this.rgbToHex(sColor[0], sColor[1], sColor[2]);

        this.dom.primaryHex.textContent = `[${this.primaryColor}] ${pHex}`;
        this.dom.secondaryHex.textContent = `[${this.secondaryColor}] ${sHex}`;

        if (this.primaryColor === 0) {
            this.dom.primaryColorChip.className = "color-chip-large transparent-zero";
            this.dom.primaryColorChip.style.backgroundColor = "transparent";
        } else {
            this.dom.primaryColorChip.className = "color-chip-large";
            this.dom.primaryColorChip.style.backgroundColor = pHex;
        }

        if (this.secondaryColor === 0) {
            this.dom.secondaryColorChip.className = "color-chip-large transparent-zero";
            this.dom.secondaryColorChip.style.backgroundColor = "transparent";
        } else {
            this.dom.secondaryColorChip.className = "color-chip-large";
            this.dom.secondaryColorChip.style.backgroundColor = sHex;
        }
    }

    swapColors() {
        const tmp = this.primaryColor;
        this.primaryColor = this.secondaryColor;
        this.secondaryColor = tmp;
        this.renderPalette();
    }

    /* ----------------------------------------------------
       Ferramentas de Desenho
       ---------------------------------------------------- */
    setTool(tool) {
        this.tool = tool;
        this.dom.toolBtns.forEach(btn => {
            btn.classList.toggle("active", btn.dataset.tool === tool);
        });

        if (tool === "stamp") {
            this.openTextStampModal();
        }
    }

    getPixel(x, y) {
        if (x < 0 || x >= this.width || y < 0 || y >= this.height) return 0;
        return this.pixels[y * this.width + x];
    }

    setPixel(x, y, colorIndex) {
        if (x < 0 || x >= this.width || y < 0 || y >= this.height) return;
        this.pixels[y * this.width + x] = colorIndex;
    }

    pushUndo() {
        this.undoStack.push([...this.pixels]);
        if (this.undoStack.length > this.maxUndo) this.undoStack.shift();
        this.redoStack = []; // Reseta redo ao fazer nova alteração
    }

    undo() {
        if (this.undoStack.length === 0) return;
        this.redoStack.push([...this.pixels]);
        this.pixels = this.undoStack.pop();
        this.renderMain();
        this.showToast("Desfeito (Undo)");
    }

    redo() {
        if (this.redoStack.length === 0) return;
        this.undoStack.push([...this.pixels]);
        this.pixels = this.redoStack.pop();
        this.renderMain();
        this.showToast("Refeito (Redo)");
    }

    revertToOriginal() {
        if (confirm("Deseja realmente reverter esta imagem ao estado original da ROM?")) {
            this.pushUndo();
            this.pixels = [...this.origPixels];
            this.renderMain();
            this.showToast("Imagem revertida ao original da ROM");
        }
    }

    clearCanvas() {
        if (confirm("Limpar todo o canvas com o Índice 0 (Transparência)?")) {
            this.pushUndo();
            this.pixels.fill(0);
            this.renderMain();
            this.showToast("Canvas limpo (Índice 0)");
        }
    }

    /* ----------------------------------------------------
       Eventos do Mouse (Desenho Pixel a Pixel)
       ---------------------------------------------------- */
    getCanvasCoords(e) {
        const rect = this.dom.viewport.getBoundingClientRect();
        const clientX = e.clientX - rect.left;
        const clientY = e.clientY - rect.top;

        const x = Math.floor((clientX - this.panX) / this.zoom);
        const y = Math.floor((clientY - this.panY) / this.zoom);
        return { x, y, rawX: clientX, rawY: clientY };
    }

    onMouseDown(e) {
        // Pan com Botão do Meio ou Barra de Espaço
        if (e.button === 1 || e.spaceKey || this.isPanning) {
            this.isPanning = true;
            this.dragStart = { x: e.clientX - this.panX, y: e.clientY - this.panY };
            this.dom.viewport.classList.add("panning");
            return;
        }

        const coords = this.getCanvasCoords(e);
        if (coords.x < 0 || coords.x >= this.width || coords.y < 0 || coords.y >= this.height) {
            return;
        }

        this.isDrawing = true;
        this.drawMouseButton = e.button; // 0 = Primária, 2 = Secundária
        this.dragStart = { x: coords.x, y: coords.y };
        const activeColor = (this.tool === "eraser") ? 0 :
                           (e.button === 2 ? this.secondaryColor : this.primaryColor);

        if (this.tool === "pencil" || this.tool === "eraser") {
            this.pushUndo();
            this.paintBrush(coords.x, coords.y, activeColor);
            this.renderMain();
        } else if (this.tool === "picker") {
            const picked = this.getPixel(coords.x, coords.y);
            this.selectColor(picked, e.button !== 2);
            this.showToast(`Cor capturada: Índice [${picked}]`);
        } else if (this.tool === "bucket") {
            this.pushUndo();
            this.floodFill(coords.x, coords.y, activeColor);
            this.renderMain();
        } else if (this.tool === "stamp" && this.textStamp) {
            this.pushUndo();
            this.stampText(coords.x, coords.y);
            this.renderMain();
            this.setTool("pencil");
        }
    }

    onMouseMove(e) {
        if (this.isPanning) {
            this.panX = e.clientX - this.dragStart.x;
            this.panY = e.clientY - this.dragStart.y;
            this.updateViewportTransform();
            return;
        }

        const coords = this.getCanvasCoords(e);
        this.currentMousePos = { x: coords.x, y: coords.y };

        // Atualiza barra de status inferior
        if (coords.x >= 0 && coords.x < this.width && coords.y >= 0 && coords.y < this.height) {
            const pIdx = this.getPixel(coords.x, coords.y);
            const tileX = Math.floor(coords.x / 8);
            const tileY = Math.floor(coords.y / 8);
            const tileNum = tileY * Math.ceil(this.width / 8) + tileX;

            this.dom.statusCoords.textContent = `X: ${coords.x}, Y: ${coords.y}`;
            this.dom.statusTile.textContent = `Tile: [${tileX}, ${tileY}] (#${tileNum})`;
            this.dom.statusColor.textContent = (pIdx === 0) ? `Índice: [0] (Transp)` : `Índice: [${pIdx}]`;
        }

        // Desenho contínuo do lápis/borracha
        if (this.isDrawing) {
            const activeColor = (this.tool === "eraser") ? 0 :
                               (this.drawMouseButton === 2 ? this.secondaryColor : this.primaryColor);

            if (this.tool === "pencil" || this.tool === "eraser") {
                this.paintLine(this.dragStart.x, this.dragStart.y, coords.x, coords.y, activeColor);
                this.dragStart = { x: coords.x, y: coords.y };
                this.renderMain();
            } else if (this.tool === "line" || this.tool === "rect" || this.tool === "rect-fill" || this.tool === "select") {
                // Desenha prévia dinâmica na camada de overlay
                this.renderOverlay();
                this.renderShapePreview(this.dragStart.x, this.dragStart.y, coords.x, coords.y, activeColor);
            }
        } else if (this.tool === "stamp") {
            this.renderOverlay();
        }
    }

    onMouseUp(e) {
        if (this.isPanning) {
            this.isPanning = false;
            this.dom.viewport.classList.remove("panning");
            return;
        }

        if (!this.isDrawing) return;
        this.isDrawing = false;

        const coords = this.getCanvasCoords(e);
        const activeColor = (this.tool === "eraser") ? 0 :
                           (this.drawMouseButton === 2 ? this.secondaryColor : this.primaryColor);

        if (this.tool === "line") {
            this.pushUndo();
            this.drawLine(this.dragStart.x, this.dragStart.y, coords.x, coords.y, activeColor);
            this.renderMain();
            this.renderOverlay();
        } else if (this.tool === "rect") {
            this.pushUndo();
            this.drawRect(this.dragStart.x, this.dragStart.y, coords.x, coords.y, activeColor, false);
            this.renderMain();
            this.renderOverlay();
        } else if (this.tool === "rect-fill") {
            this.pushUndo();
            this.drawRect(this.dragStart.x, this.dragStart.y, coords.x, coords.y, activeColor, true);
            this.renderMain();
            this.renderOverlay();
        } else if (this.tool === "select") {
            const sx = Math.min(this.dragStart.x, coords.x);
            const sy = Math.min(this.dragStart.y, coords.y);
            const sw = Math.abs(coords.x - this.dragStart.x) + 1;
            const sh = Math.abs(coords.y - this.dragStart.y) + 1;
            this.selection = { x: sx, y: sy, w: sw, h: sh };
            this.renderOverlay();
        }
    }

    onWheel(e) {
        e.preventDefault();
        const zoomDelta = e.deltaY < 0 ? 1.25 : 0.8;
        this.setZoom(this.zoom * zoomDelta, e.clientX, e.clientY);
    }

    /* ----------------------------------------------------
       Algoritmos de Desenho Pixel Art
       ---------------------------------------------------- */
    paintBrush(x, y, colorIndex) {
        if (this.brushSize === 1) {
            this.setPixel(x, y, colorIndex);
        } else {
            // Pincel 2x2
            this.setPixel(x, y, colorIndex);
            this.setPixel(x + 1, y, colorIndex);
            this.setPixel(x, y + 1, colorIndex);
            this.setPixel(x + 1, y + 1, colorIndex);
        }
    }

    // Algoritmo de Linha Bresenham
    drawLine(x0, y0, x1, y1, colorIndex) {
        const dx = Math.abs(x1 - x0);
        const dy = Math.abs(y1 - y0);
        const sx = (x0 < x1) ? 1 : -1;
        const sy = (y0 < y1) ? 1 : -1;
        let err = dx - dy;

        while (true) {
            this.paintBrush(x0, y0, colorIndex);
            if (x0 === x1 && y0 === y1) break;
            const e2 = 2 * err;
            if (e2 > -dy) {
                err -= dy;
                x0 += sx;
            }
            if (e2 < dx) {
                err += dx;
                y0 += sy;
            }
        }
    }

    paintLine(x0, y0, x1, y1, colorIndex) {
        this.drawLine(x0, y0, x1, y1, colorIndex);
    }

    drawRect(x0, y0, x1, y1, colorIndex, filled = false) {
        const sx = Math.min(x0, x1);
        const sy = Math.min(y0, y1);
        const ex = Math.max(x0, x1);
        const ey = Math.max(y0, y1);

        if (filled) {
            for (let y = sy; y <= ey; y++) {
                for (let x = sx; x <= ex; x++) {
                    this.setPixel(x, y, colorIndex);
                }
            }
        } else {
            for (let x = sx; x <= ex; x++) {
                this.setPixel(x, sy, colorIndex);
                this.setPixel(x, ey, colorIndex);
            }
            for (let y = sy; y <= ey; y++) {
                this.setPixel(sx, y, colorIndex);
                this.setPixel(ex, y, colorIndex);
            }
        }
    }

    // Flood Fill 4-Way
    floodFill(startX, startY, targetColor) {
        const sourceColor = this.getPixel(startX, startY);
        if (sourceColor === targetColor) return;

        const queue = [{ x: startX, y: startY }];
        const visited = new Uint8Array(this.width * this.height);

        while (queue.length > 0) {
            const { x, y } = queue.pop();
            const idx = y * this.width + x;

            if (x < 0 || x >= this.width || y < 0 || y >= this.height) continue;
            if (visited[idx]) continue;
            visited[idx] = 1;

            if (this.pixels[idx] === sourceColor) {
                this.pixels[idx] = targetColor;
                queue.push({ x: x + 1, y: y });
                queue.push({ x: x - 1, y: y });
                queue.push({ x: x, y: y + 1 });
                queue.push({ x: x, y: y - 1 });
            }
        }
    }

    renderShapePreview(x0, y0, x1, y1, colorIndex) {
        const ctx = this.dom.ctxOverlay;
        const color = this.palette[colorIndex] || [255, 255, 255];
        ctx.fillStyle = `rgb(${color[0]}, ${color[1]}, ${color[2]})`;

        if (this.tool === "line") {
            const dx = Math.abs(x1 - x0);
            const dy = Math.abs(y1 - y0);
            const sx = (x0 < x1) ? 1 : -1;
            const sy = (y0 < y1) ? 1 : -1;
            let err = dx - dy;
            let cx = x0, cy = y0;

            while (true) {
                ctx.fillRect(cx, cy, 1, 1);
                if (cx === x1 && cy === y1) break;
                const e2 = 2 * err;
                if (e2 > -dy) { err -= dy; cx += sx; }
                if (e2 < dx) { err += dx; cy += sy; }
            }
        } else if (this.tool === "rect" || this.tool === "rect-fill") {
            const sx = Math.min(x0, x1);
            const sy = Math.min(y0, y1);
            const sw = Math.abs(x1 - x0) + 1;
            const sh = Math.abs(y1 - y0) + 1;
            if (this.tool === "rect-fill") {
                ctx.fillRect(sx, sy, sw, sh);
            } else {
                ctx.fillRect(sx, sy, sw, 1);
                ctx.fillRect(sx, sy + sh - 1, sw, 1);
                ctx.fillRect(sx, sy, 1, sh);
                ctx.fillRect(sx + sw - 1, sy, 1, sh);
            }
        }
    }

    /* ----------------------------------------------------
       Carimbador de Texto (Pixel Text Stamping)
       ---------------------------------------------------- */
    openTextStampModal() {
        if (this.currentAsset && this.currentAsset.sugg_text) {
            this.dom.textStampInput.value = this.currentAsset.sugg_text.split(/<br>|\n/)[0].replace(/`/g, "").trim();
        }
        this.dom.textStampModal.classList.add("active");
        this.dom.textStampInput.focus();
    }

    closeTextStampModal() {
        this.dom.textStampModal.classList.remove("active");
    }

    prepareTextStamp() {
        const text = this.dom.textStampInput.value.trim();
        if (!text) {
            this.closeTextStampModal();
            return;
        }

        const font = this.dom.textStampFontSelect.value;
        const addShadow = this.dom.textStampShadowCheck.checked;

        // Renderiza matriz de texto
        this.textStamp = renderPixelText(text, {
            font: font,
            textColorIndex: this.primaryColor,
            shadowColorIndex: this.secondaryColor,
            addShadow: addShadow,
            shadowType: "drop"
        });

        this.closeTextStampModal();
        this.showToast(`Carimbo de texto pronto: "${text}". Clique no canvas para posicionar.`);
    }

    stampText(startX, startY) {
        if (!this.textStamp) return;
        const tw = this.textStamp.width;
        const th = this.textStamp.height;

        for (let y = 0; y < th; y++) {
            for (let x = 0; x < tw; x++) {
                const cIdx = this.textStamp.grid[y][x];
                if (cIdx >= 0) {
                    this.setPixel(startX + x, startY + y, cIdx);
                }
            }
        }
        this.textStamp = null;
        this.showToast("Texto carimbado com sucesso! Use o lápis para refinar.");
    }

    /* ----------------------------------------------------
       Salvar no Projeto & Download
       ---------------------------------------------------- */
    async saveToProject() {
        if (!this.currentAsset) return;

        this.dom.saveBtn.disabled = true;
        this.dom.saveBtn.textContent = "⏳ Salvando...";

        try {
            const payload = {
                game: this.game,
                id: this.currentAsset.id,
                rel_path: this.relPath || this.currentAsset.filename,
                width: this.width,
                height: this.height,
                palette: this.palette,
                pixels: this.pixels,
                mark_completed: true
            };

            const res = await fetch("/api/save_image", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(payload)
            });

            if (!res.ok) {
                const err = await res.json();
                throw new Error(err.error || "Erro no salvamento.");
            }

            const data = await res.json();
            this.showToast(`✅ Salvo em ${data.saved_path} (${data.bytes} B)!`, "success");

            // Atualiza status local
            this.currentAsset.status = "✅ Editado";
            this.dom.activeAssetStatus.textContent = "✅ Editado";
            this.dom.activeAssetStatus.className = "asset-status-pill status-done";

            // Atualiza na lista de cards
            this.renderCatalogList();
        } catch (err) {
            this.showToast("Erro ao salvar: " + err.message, "error");
        } finally {
            this.dom.saveBtn.disabled = false;
            this.dom.saveBtn.innerHTML = `💾 Salvar no Projeto <span style="font-size:10px;opacity:0.8;">(Ctrl+S)</span>`;
        }
    }

    downloadPNG() {
        // Gera download direto pelo browser
        const tempCanvas = document.createElement("canvas");
        tempCanvas.width = this.width;
        tempCanvas.height = this.height;
        const ctx = tempCanvas.getContext("2d");
        ctx.imageSmoothingEnabled = false;
        ctx.drawImage(this.dom.canvasMain, 0, 0);

        const a = document.createElement("a");
        a.href = tempCanvas.toDataURL("image/png");
        a.download = (this.currentAsset ? this.currentAsset.id + "_" : "") + "editado.png";
        a.click();
        this.showToast("PNG exportado para download!");
    }

    /* ----------------------------------------------------
       Teclado & Atalhos
       ---------------------------------------------------- */
    onKeyDown(e) {
        // Se estiver em input de texto, não intercepta atalhos
        if (e.target.tagName === "INPUT" || e.target.tagName === "SELECT") return;

        // Salvar (Ctrl+S)
        if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === "s") {
            e.preventDefault();
            this.saveToProject();
            return;
        }

        // Desfazer (Ctrl+Z) / Refazer (Ctrl+Y)
        if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === "z") {
            e.preventDefault();
            if (e.shiftKey) this.redo();
            else this.undo();
            return;
        }
        if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === "y") {
            e.preventDefault();
            this.redo();
            return;
        }

        // Atalhos de Ferramentas
        const k = e.key.toLowerCase();
        if (k === "b" || k === "p") this.setTool("pencil");
        else if (k === "e") this.setTool("eraser");
        else if (k === "i") this.setTool("picker");
        else if (k === "f" || k === "g") this.setTool("bucket");
        else if (k === "l") this.setTool("line");
        else if (k === "r") this.setTool("rect");
        else if (k === "u") this.setTool("rect-fill");
        else if (k === "m") this.setTool("select");
        else if (k === "t") this.setTool("stamp");
        else if (k === "x") this.swapColors();
        else if (k === "c") this.resetView();

        // Navegação de catálogo com [ e ]
        else if (e.key === "[") this.navigateCatalog(-1);
        else if (e.key === "]") this.navigateCatalog(1);

        // Espiar Imagem Original com Tab ou Espaço (Segurar)
        else if (e.key === "Tab" || e.key === " ") {
            e.preventDefault();
            if (!this.peekOriginal) {
                this.peekOriginal = true;
                this.renderBase();
                this.renderMain();
            }
        }

        // Atalhos numéricos 0 a 9 para trocar de cor da paleta
        else if (/^[0-9]$/.test(e.key)) {
            const num = parseInt(e.key, 10);
            this.selectColor(num, true);
        }
    }

    onKeyUp(e) {
        if (e.key === "Tab" || e.key === " ") {
            if (this.peekOriginal) {
                this.peekOriginal = false;
                this.renderBase();
                this.renderMain();
            }
        }
    }

    /* ----------------------------------------------------
       Utilitários
       ---------------------------------------------------- */
    rgbToHex(r, g, b) {
        return "#" + [r, g, b].map(x => {
            const hex = x.toString(16);
            return hex.length === 1 ? "0" + hex : hex;
        }).join("");
    }

    showToast(message, type = "normal") {
        const toast = document.createElement("div");
        toast.className = `toast ${type === "success" ? "toast-success" : (type === "error" ? "toast-error" : "")}`;
        toast.innerHTML = `<span>${message}</span>`;
        this.dom.toastContainer.appendChild(toast);
        setTimeout(() => {
            toast.style.opacity = "0";
            toast.style.transition = "opacity 0.3s";
            setTimeout(() => toast.remove(), 300);
        }, 3200);
    }
}

// Inicializa a aplicação ao carregar
window.addEventListener("DOMContentLoaded", () => {
    window.app = new GBAEditor();
});
