const API = ''

// ============ ЛОГИН ============

document.getElementById('loginForm').addEventListener('submit', async function(e) {
    e.preventDefault()
    const username = document.getElementById('loginUsername').value
    const password = document.getElementById('loginPassword').value

    const formData = new FormData()
    formData.append('username', username)
    formData.append('password', password)

    const res = await fetch(`${API}/api/auth/login`, {
        method: 'POST',
        body: formData,
        credentials: 'include'
    })

    if (res.ok) {
        document.getElementById('loginPage').classList.add('hidden')
        document.getElementById('mainPage').classList.remove('hidden')
        showSection('genres')
    } else {
        document.getElementById('loginError').textContent = 'Неверный логин или пароль'
    }
})

// ============ ВЫХОД ============

async function logout() {
    await fetch(`${API}/api/auth/logout`, {
        method: 'POST',
        credentials: 'include'
    })
    document.getElementById('mainPage').classList.add('hidden')
    document.getElementById('loginPage').classList.remove('hidden')
}

// ============ НАВИГАЦИЯ ============

function showSection(name) {
    document.getElementById('genresSection').classList.add('hidden')
    document.getElementById('moviesSection').classList.add('hidden')
    document.getElementById(name + 'Section').classList.remove('hidden')
    if (name === 'genres') loadGenres()
    if (name === 'movies') loadMovies()
}

// ============ ЖАНРЫ ============

async function loadGenres() {
    const res = await fetch(`${API}/api/genres`, { credentials: 'include' })
    const genres = await res.json()

    // Заполняем таблицу
    const tbody = document.getElementById('genresList')
    tbody.innerHTML = ''
    genres.forEach(g => {
        tbody.innerHTML += `
            <tr>
                <td>${g.id}</td>
                <td>${g.name}</td>
                <td>${g.description || ''}</td>
                <td>
                    <button class="btn-edit" onclick="editGenre(${g.id}, '${g.name}', '${g.description || ''}')">Изменить</button>
                    <button class="btn-delete" onclick="deleteGenre(${g.id})">Удалить</button>
                </td>
            </tr>
        `
    })

    // Заполняем выпадающие списки в фильтрах и форме фильмов
    const filterGenre = document.getElementById('filterGenre')
    const movieGenre = document.getElementById('movieGenre')
    filterGenre.innerHTML = '<option value="">Все жанры</option>'
    movieGenre.innerHTML = '<option value="">Выберите жанр</option>'
    genres.forEach(g => {
        filterGenre.innerHTML += `<option value="${g.id}">${g.name}</option>`
        movieGenre.innerHTML += `<option value="${g.id}">${g.name}</option>`
    })
}

document.getElementById('genreForm').addEventListener('submit', async function(e) {
    e.preventDefault()
    const id = document.getElementById('genreId').value
    const name = document.getElementById('genreName').value
    const description = document.getElementById('genreDescription').value

    const formData = new FormData()
    formData.append('name', name)
    formData.append('description', description)

    if (id) {
        await fetch(`${API}/api/genres/${id}`, {
            method: 'PUT',
            body: formData,
            credentials: 'include'
        })
    } else {
        await fetch(`${API}/api/genres`, {
            method: 'POST',
            body: formData,
            credentials: 'include'
        })
    }

    resetGenreForm()
    loadGenres()
})

function editGenre(id, name, description) {
    document.getElementById('genreId').value = id
    document.getElementById('genreName').value = name
    document.getElementById('genreDescription').value = description
}

function resetGenreForm() {
    document.getElementById('genreId').value = ''
    document.getElementById('genreName').value = ''
    document.getElementById('genreDescription').value = ''
}

async function deleteGenre(id) {
    if (!confirm('Удалить жанр?')) return
    const res = await fetch(`${API}/api/genres/${id}`, {
        method: 'DELETE',
        credentials: 'include'
    })
    const data = await res.json()
    if (!res.ok) {
        alert(data.detail)
    }
    loadGenres()
}

// ============ ФИЛЬМЫ ============

async function loadMovies() {
    const search = document.getElementById('searchMovie').value
    const genreId = document.getElementById('filterGenre').value
    const yearFrom = document.getElementById('yearFrom').value
    const yearTo = document.getElementById('yearTo').value

    let url = `${API}/api/movies?search=${search}`
    if (genreId) url += `&genre_id=${genreId}`
    if (yearFrom) url += `&year_from=${yearFrom}`
    if (yearTo) url += `&year_to=${yearTo}`

    const res = await fetch(url, { credentials: 'include' })
    const movies = await res.json()

    const tbody = document.getElementById('moviesList')
    tbody.innerHTML = ''
    movies.forEach(m => {
        const poster = m.poster_path
            ? `<img src="${API}/${m.poster_path}" class="poster-thumb">`
            : 'Нет'
        const trailer = m.trailer_path
            ? `<video src="${API}/${m.trailer_path}" width="120" controls></video>`
            : 'Нет'
        tbody.innerHTML += `
            <tr>
                <td>${poster}</td>
                <td>${m.title}</td>
                <td>${m.genre_name || ''}</td>
                <td>${m.release_year}</td>
                <td>${trailer}</td>
                <td>
                    <button class="btn-edit" onclick="editMovie(${m.id})">Изменить</button>
                    <button class="btn-delete" onclick="deleteMovie(${m.id})">Удалить</button>
                </td>
            </tr>
        `
    })
}

document.getElementById('movieForm').addEventListener('submit', async function(e) {
    e.preventDefault()
    const id = document.getElementById('movieId').value
    const formData = new FormData()
    formData.append('title', document.getElementById('movieTitle').value)
    formData.append('description', document.getElementById('movieDescription').value)
    formData.append('release_year', document.getElementById('movieYear').value)
    formData.append('genre_id', document.getElementById('movieGenre').value)

    const poster = document.getElementById('moviePoster').files[0]
    const trailer = document.getElementById('movieTrailer').files[0]
    if (poster) formData.append('poster', poster)
    if (trailer) formData.append('trailer', trailer)

    if (id) {
        await fetch(`${API}/api/movies/${id}`, {
            method: 'PUT',
            body: formData,
            credentials: 'include'
        })
    } else {
        await fetch(`${API}/api/movies`, {
            method: 'POST',
            body: formData,
            credentials: 'include'
        })
    }

    resetMovieForm()
    loadMovies()
})

async function editMovie(id) {
    const res = await fetch(`${API}/api/movies/${id}`, { credentials: 'include' })
    // Берём из уже загруженного списка
    const allRes = await fetch(`${API}/api/movies`, { credentials: 'include' })
    const all = await allRes.json()
    const m = all.find(x => x.id === id)
    if (!m) return

    document.getElementById('movieId').value = m.id
    document.getElementById('movieTitle').value = m.title
    document.getElementById('movieDescription').value = m.description || ''
    document.getElementById('movieYear').value = m.release_year
    document.getElementById('movieGenre').value = m.genre_id
}

function resetMovieForm() {
    document.getElementById('movieId').value = ''
    document.getElementById('movieTitle').value = ''
    document.getElementById('movieDescription').value = ''
    document.getElementById('movieYear').value = ''
    document.getElementById('movieGenre').value = ''
    document.getElementById('moviePoster').value = ''
    document.getElementById('movieTrailer').value = ''
}

async function deleteMovie(id) {
    if (!confirm('Удалить фильм?')) return
    await fetch(`${API}/api/movies/${id}`, {
        method: 'DELETE',
        credentials: 'include'
    })
    loadMovies()
}

app.mount("/", StaticFiles(directory="frontend", html=True), name="frontend")