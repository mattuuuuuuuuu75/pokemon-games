(function () {
    const FS_PREF_KEY = 'pokemon_games_fullscreen_pref';
    let isUnloading = false;

    window.addEventListener('beforeunload', () => { isUnloading = true; });
    window.addEventListener('pagehide', () => { isUnloading = true; });
    document.addEventListener('click', (e) => {
        const link = e.target.closest && e.target.closest('a[href]');
        if (link) isUnloading = true;
    }, true);

    function getFsElement() {
        return document.fullscreenElement ||
               document.webkitFullscreenElement ||
               document.mozFullScreenElement ||
               document.msFullscreenElement ||
               null;
    }

    function isFsSupported() {
        const el = document.documentElement;
        return Boolean(
            el.requestFullscreen ||
            el.webkitRequestFullscreen ||
            el.mozRequestFullScreen ||
            el.msRequestFullscreen
        );
    }

    function isStandalonePWA() {
        return window.matchMedia('(display-mode: standalone)').matches ||
               window.navigator.standalone === true;
    }

    async function enterFullscreen(silent = false) {
        const el = document.documentElement;
        try {
            if (el.requestFullscreen) {
                await el.requestFullscreen({ navigationUI: 'hide' });
            } else if (el.webkitRequestFullscreen) {
                el.webkitRequestFullscreen();
            } else if (el.msRequestFullscreen) {
                el.msRequestFullscreen();
            } else if (!silent) {
                showIosFullscreenGuide();
                return false;
            }
            try { sessionStorage.setItem(FS_PREF_KEY, '1'); } catch (_) {}
            updateAllFsButtons();
            triggerLayoutRefresh();
            return true;
        } catch (_) {
            if (!silent && !isFsSupported()) {
                showIosFullscreenGuide();
            }
            return false;
        }
    }

    async function exitFullscreen() {
        try { sessionStorage.removeItem(FS_PREF_KEY); } catch (_) {}
        try {
            if (document.exitFullscreen) {
                await document.exitFullscreen();
            } else if (document.webkitExitFullscreen) {
                document.webkitExitFullscreen();
            } else if (document.msExitFullscreen) {
                document.msExitFullscreen();
            }
        } catch (_) {}
        updateAllFsButtons();
        triggerLayoutRefresh();
    }

    window.toggleGameFullscreen = function () {
        if (getFsElement()) {
            exitFullscreen();
        } else {
            enterFullscreen(false);
        }
    };

    function triggerLayoutRefresh() {
        setTimeout(() => {
            window.dispatchEvent(new Event('resize'));
        }, 80);
        setTimeout(() => {
            window.dispatchEvent(new Event('resize'));
        }, 280);
    }

    function updateAllFsButtons() {
        const active = Boolean(getFsElement());
        document.querySelectorAll('.fs-toggle-btn').forEach((btn) => {
            const mode = btn.getAttribute('data-fs-mode') || 'normal';
            if (mode === 'icon') {
                btn.innerHTML = active ? '🗗' : '⛶';
                btn.title = active ? 'ぜんがめんを もどす' : 'ぜんがめんに する';
            } else if (mode === 'portal') {
                btn.innerHTML = active
                    ? '<span>🗗</span><span>ふつうの がめんサイズに もどす</span>'
                    : '<span>⛶</span><span>ぜんがめん（フルスクリーン）で おおきく あそぶ！</span>';
            } else if (mode === 'kana') {
                btn.innerHTML = active
                    ? '<span>🗗</span><span>もどす</span>'
                    : '<span>⛶</span><span>ぜんがめん</span>';
            } else {
                btn.innerHTML = active
                    ? '<span>🗗</span><span class="hidden sm:inline">戻す</span>'
                    : '<span>⛶</span><span class="hidden sm:inline">全画面</span>';
            }

            if (active) {
                btn.classList.add('ring-2', 'ring-yellow-300');
            } else {
                btn.classList.remove('ring-2', 'ring-yellow-300');
            }
        });
    }

    function showIosFullscreenGuide() {
        if (isStandalonePWA()) return;
        let modal = document.getElementById('iosFsGuideModal');
        if (!modal) {
            modal = document.createElement('div');
            modal.id = 'iosFsGuideModal';
            modal.className = 'fixed inset-0 z-[9999] bg-black/85 backdrop-blur-sm flex items-center justify-center p-4';
            modal.innerHTML = `
                <div class="bg-slate-900 border-4 border-yellow-300 rounded-3xl p-5 max-w-sm w-full text-center space-y-3 text-white shadow-2xl">
                    <div class="text-4xl">📱✨</div>
                    <div class="text-lg font-black text-yellow-300">ぜんがめんで あそぶ ほうほう！</div>
                    <p class="text-xs sm:text-sm font-bold text-slate-200 leading-relaxed">
                        iPhone / Safari では、した（または うえ）の <span class="text-cyan-300 font-black">きょうゆうボタン［↑］</span> から<br>
                        <span class="bg-yellow-300 text-black px-2 py-0.5 rounded font-black">「ホームがめんに ついか」</span> をえらぶと、いつでも ぜんがめんアプリで あそべるよ！
                    </p>
                    <button onclick="document.getElementById('iosFsGuideModal').remove()" class="w-full py-2.5 rounded-2xl bg-gradient-to-r from-yellow-300 to-amber-400 text-black font-black text-sm border-2 border-white shadow">
                        わかった！ とじる
                    </button>
                </div>
            `;
            document.body.appendChild(modal);
        }
    }

    ['fullscreenchange', 'webkitfullscreenchange', 'mozfullscreenchange', 'MSFullscreenChange'].forEach((ev) => {
        document.addEventListener(ev, () => {
            if (!getFsElement() && !isUnloading) {
                // ユーザーがEscキー等で解除した場合は設定もクリア
                try { sessionStorage.removeItem(FS_PREF_KEY); } catch (_) {}
            }
            updateAllFsButtons();
            triggerLayoutRefresh();
        });
    });

    // PC向け F キーショートカット（文字入力中を除く）
    window.addEventListener('keydown', (e) => {
        if (e.key === 'f' || e.key === 'F') {
            const tag = (document.activeElement && document.activeElement.tagName) || '';
            if (tag === 'INPUT' || tag === 'TEXTAREA' || e.ctrlKey || e.metaKey || e.altKey) return;
            e.preventDefault();
            window.toggleGameFullscreen();
        }
    });

    // 前の画面で全画面モードだった場合、次のゲーム画面での最初のタッチで自動的に全画面を継続！
    function tryAutoRestoreOnFirstGesture(e) {
        if (getFsElement()) return;
        const closeBtn = e.target.closest && e.target.closest('.fs-toggle-btn');
        if (closeBtn) return;
        let want = false;
        try { want = sessionStorage.getItem(FS_PREF_KEY) === '1'; } catch (_) {}
        if (want && isFsSupported()) {
            enterFullscreen(true);
        }
    }
    window.addEventListener('pointerup', tryAutoRestoreOnFirstGesture, { passive: true });

    window.addEventListener('DOMContentLoaded', () => {
        updateAllFsButtons();
    });
})();
