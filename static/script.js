document.addEventListener('DOMContentLoaded', () => {
  // State
  let currentEra = 0;
  let currentTag = 'all';
  let currentMeta = null;
  let activeVideo = null;
  let favorites = JSON.parse(localStorage.getItem('yt_trash_favs') || '[]');

  // DOM Elements
  const queryInput = document.getElementById('queryInput');
  const btnRollQuery = document.getElementById('btnRollQuery');
  const metaMap = document.getElementById('metaMap');
  const metaCategory = document.getElementById('metaCategory');
  const metaDesc = document.getElementById('metaDesc');
  const btnOpenYT = document.getElementById('btnOpenYT');
  
  const categorySelect = document.getElementById('categorySelect');
  const maxViewsSelect = document.getElementById('maxViewsSelect');
  const eraButtons = document.querySelectorAll('.era-btn');

  const btnDeepScan = document.getElementById('btnDeepScan');
  const btnRoulette = document.getElementById('btnRoulette');
  const btnToggleFavorites = document.getElementById('btnToggleFavorites');
  const favCount = document.getElementById('favCount');

  const playerSection = document.getElementById('playerSection');
  const videoIframe = document.getElementById('videoIframe');
  const playerTitle = document.getElementById('playerTitle');
  const playerChannel = document.getElementById('playerChannel');
  const playerViews = document.getElementById('playerViews');
  const playerDate = document.getElementById('playerDate');
  const btnClosePlayer = document.getElementById('btnClosePlayer');
  const btnFavCurrent = document.getElementById('btnFavCurrent');
  const playerYtLink = document.getElementById('playerYtLink');
  const playerDownload = document.getElementById('playerDownload');

  const loadingState = document.getElementById('loadingState');
  const loadingText = document.getElementById('loadingText');
  const videoGrid = document.getElementById('videoGrid');
  const emptyState = document.getElementById('emptyState');
  const resultsCount = document.getElementById('resultsCount');
  const resultsHeading = document.getElementById('resultsHeading');

  const favoritesModal = document.getElementById('favoritesModal');
  const btnCloseFavorites = document.getElementById('btnCloseFavorites');
  const favoritesList = document.getElementById('favoritesList');

  // Update favorites count badge
  function updateFavBadge() {
    favCount.textContent = favorites.length;
  }
  updateFavBadge();

  // Switch Era Tabs
  eraButtons.forEach(btn => {
    btn.addEventListener('click', () => {
      eraButtons.forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      currentEra = parseInt(btn.dataset.era);
      rollNewQuery();
    });
  });

  // Switch Category
  categorySelect.addEventListener('change', (e) => {
    currentTag = e.target.value;
    rollNewQuery();
  });

  // Roll new query
  async function rollNewQuery() {
    try {
      const res = await fetch(`/api/generate?era=${currentEra}&tag=${currentTag}`);
      const data = await res.json();
      if (data.queries && data.queries.length > 0) {
        currentMeta = data.queries[0];
        queryInput.value = currentMeta.query;
        
        metaMap.textContent = currentMeta.map_label || `map ${currentMeta.map}`;
        metaCategory.textContent = currentMeta.tag_labels.join(' / ');
        metaDesc.textContent = currentMeta.raw_description;
        btnOpenYT.href = currentMeta.youtube_url;
      }
    } catch (err) {
      console.error("error:", err);
    }
  }

  btnRollQuery.addEventListener('click', rollNewQuery);

  // Manual query input change
  queryInput.addEventListener('input', () => {
    const q = queryInput.value.trim();
    if (q) {
      btnOpenYT.href = `https://www.youtube.com/results?search_query=${encodeURIComponent(q)}`;
    }
  });

  // Deep Scan
  btnDeepScan.addEventListener('click', async () => {
    const query = queryInput.value.trim();
    const maxViews = parseInt(maxViewsSelect.value);

    setLoading(true, `searching ${query}`);

    try {
      const params = new URLSearchParams({
        query: query,
        era: currentEra,
        tag: currentTag,
        max_views: maxViews,
        limit: 15
      });

      const res = await fetch(`/api/search?${params.toString()}`);
      const data = await res.json();

      setLoading(false);
      renderResults(data.videos, data.query);
      resultsHeading.scrollIntoView({ behavior: 'smooth', block: 'start' });
    } catch (err) {
      setLoading(false);
      alert('error, check the console ig');
      console.error(err);
    }
  });

  // Roulette (Instant Video)
  btnRoulette.addEventListener('click', async () => {
    const maxViews = parseInt(maxViewsSelect.value);
    setLoading(true, "crawling youtube for the hidden gem");

    try {
      const params = new URLSearchParams({
        era: currentEra,
        tag: currentTag,
        max_views: maxViews
      });

      const res = await fetch(`/api/roulette?${params.toString()}`);
      const data = await res.json();
      setLoading(false);

      if (data.success && data.video) {
        // Запускаем видео в плеере
        playVideo(data.video);
        // Добавляем карточку в начало сетки
        prependVideoCard(data.video);
      } else {
        alert(data.message || 'try again plz');
      }
    } catch (err) {
      setLoading(false);
      alert('error');
      console.error(err);
    }
  });

  function setLoading(isLoading, text = "") {
    if (isLoading) {
      loadingText.textContent = text;
      loadingState.classList.remove('hidden');
      emptyState.classList.add('hidden');
    } else {
      loadingState.classList.add('hidden');
    }
  }

  function renderResults(videos, searchedQuery) {
    videoGrid.innerHTML = '';

    if (!videos || videos.length === 0) {
      emptyState.classList.remove('hidden');
      resultsCount.textContent = '0 videos';
      resultsHeading.textContent = `nothing was found. try again (${searchedQuery})`;
      return;
    }

    emptyState.classList.add('hidden');
    resultsCount.textContent = `${videos.length} videos`;
    resultsHeading.textContent = `i found something (${searchedQuery})`;

    videos.forEach(v => {
      const card = createVideoCard(v);
      videoGrid.appendChild(card);
    });
  }

  function prependVideoCard(v) {
    emptyState.classList.add('hidden');
    const existing = videoGrid.querySelector(`[data-id="${v.id}"]`);
    if (!existing) {
      const card = createVideoCard(v);
      videoGrid.prepend(card);
    }
  }

  function createVideoCard(video) {
    const card = document.createElement('div');
    card.className = 'video-card';
    card.dataset.id = video.id;

    const viewsText = video.views === 0 ? '0 views' : `${video.views} views`;

    card.innerHTML = `
      <div class="thumb-wrap">
        <img src="${video.thumbnail}" alt="${escapeHtml(video.title)}" loading="lazy">
        <span class="card-badge-views">${viewsText}</span>
        <span class="card-badge-duration">${video.duration}</span>
      </div>
      <div class="card-body">
        <h4 class="card-title" title="${escapeHtml(video.title)}">${escapeHtml(video.title)}</h4>
        <div class="card-uploader">${escapeHtml(video.uploader)}</div>
        <div class="card-footer">
          <span>${video.upload_date}</span>
          <span class="card-matched-query">${escapeHtml(video.matched_query || '')}</span>
        </div>
      </div>
    `;

    card.addEventListener('click', () => {
      playVideo(video);
    });

    return card;
  }

  function playVideo(video) {
    activeVideo = video;
    videoIframe.src = video.embed_url;
    playerTitle.textContent = video.title;
    playerChannel.textContent = `author: ${video.uploader}`;
    playerViews.textContent = `${video.views} views`;
    playerDate.textContent = `${video.upload_date || '??.??.????'}`;
    playerYtLink.href = video.url;
    playerDownload.href = `/api/download/${video.id}?title=${encodeURIComponent(video.title)}`;

    // Check if in favorites
    checkFavButtonState();

    playerSection.classList.remove('hidden');
    playerSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
  }

  btnClosePlayer.addEventListener('click', () => {
    videoIframe.src = "";
    playerSection.classList.add('hidden');
    activeVideo = null;
  });

  // Favorites logic
  function checkFavButtonState() {
    if (!activeVideo) return;
    const isFav = favorites.some(f => f.id === activeVideo.id);
    if (isFav) {
      btnFavCurrent.textContent = 'yes';
      btnFavCurrent.style.background = 'var(--accent-gold)';
      btnFavCurrent.style.color = '#000';
    } else {
      btnFavCurrent.textContent = 'loves it';
      btnFavCurrent.style.background = 'rgba(255, 183, 3, 0.15)';
      btnFavCurrent.style.color = 'var(--accent-gold)';
    }
  }

  btnFavCurrent.addEventListener('click', () => {
    if (!activeVideo) return;
    const index = favorites.findIndex(f => f.id === activeVideo.id);
    if (index >= 0) {
      favorites.splice(index, 1);
    } else {
      favorites.unshift(activeVideo);
    }
    localStorage.setItem('yt_trash_favs', JSON.stringify(favorites));
    updateFavBadge();
    checkFavButtonState();
  });

  // Favorites Modal
  btnToggleFavorites.addEventListener('click', () => {
    renderFavoritesList();
    favoritesModal.classList.remove('hidden');
  });

  btnCloseFavorites.addEventListener('click', () => {
    favoritesModal.classList.add('hidden');
  });

  favoritesModal.addEventListener('click', (e) => {
    if (e.target === favoritesModal) {
      favoritesModal.classList.add('hidden');
    }
  });

  function renderFavoritesList() {
    favoritesList.innerHTML = '';
    if (favorites.length === 0) {
      favoritesList.innerHTML = '<p style="color:var(--text-muted); text-align:center; padding:20px;">nothing here but us, chickens!</p>';
      return;
    }

    favorites.forEach((v, idx) => {
      const item = document.createElement('div');
      item.className = 'fav-item';
      item.innerHTML = `
        <img class="fav-thumb" src="${v.thumbnail}">
        <div class="fav-info">
          <div class="fav-title">${escapeHtml(v.title)}</div>
          <div class="fav-meta">${v.views} views - ${escapeHtml(v.uploader)}</div>
        </div>
        <button class="btn-remove-fav" title="remove">&times;</button>
      `;

      item.querySelector('.fav-info').addEventListener('click', () => {
        playVideo(v);
        favoritesModal.classList.add('hidden');
      });

      item.querySelector('.btn-remove-fav').addEventListener('click', (e) => {
        e.stopPropagation();
        favorites.splice(idx, 1);
        localStorage.setItem('yt_trash_favs', JSON.stringify(favorites));
        updateFavBadge();
        renderFavoritesList();
        checkFavButtonState();
      });

      favoritesList.appendChild(item);
    });
  }

  function escapeHtml(str) {
    if (!str) return '';
    return str.replace(/[&<>"']/g, function(m) {
      return {
        '&': '&amp;',
        '<': '&lt;',
        '>': '&gt;',
        '"': '&quot;',
        "'": '&#039;'
      }[m];
    });
  }

  // Load initial query
  rollNewQuery();
});
