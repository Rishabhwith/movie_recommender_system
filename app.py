import streamlit as st
import pickle
import pandas as pd
import requests
from concurrent.futures import ThreadPoolExecutor
import re

# ------------------- Config -------------------
TMDB_API_KEY = "8265bd1679663a7ea12ac168da84d2e8"
POSTER_SIZE = "w342"
RECOMMEND_COUNT = 5

# ------------------- Helper Functions -------------------
@st.cache_data(show_spinner=False)
def fetch_poster(movie_id):
    try:
        movie_id = int(movie_id)
        url = f"https://api.themoviedb.org/3/movie/{movie_id}?api_key={TMDB_API_KEY}&language=en-US"
        response = requests.get(url, timeout=5)
        data = response.json()
        if data.get('poster_path'):
            return f"https://image.tmdb.org/t/p/{POSTER_SIZE}" + data['poster_path']
    except:
        pass
    return "https://via.placeholder.com/342x513?text=No+Image"

@st.cache_data(show_spinner=False)
def fetch_movie_details(movie_id):
    details = {
        "title": "No Title",
        "overview": "No description available.",
        "rating": "N/A",
        "release_date": "N/A",
        "poster": "https://via.placeholder.com/342x513?text=No+Image"
    }
    try:
        movie_id = int(movie_id)
        url = f"https://api.themoviedb.org/3/movie/{movie_id}?api_key={TMDB_API_KEY}&language=en-US"
        response = requests.get(url, timeout=5)
        data = response.json()
        details.update({
            "title": data.get("title", details["title"]),
            "overview": data.get("overview", details["overview"]),
            "rating": data.get("vote_average", details["rating"]),
            "release_date": data.get("release_date", details["release_date"]),
            "poster": f"https://image.tmdb.org/t/p/{POSTER_SIZE}" + data['poster_path'] if data.get('poster_path') else details["poster"]
        })
    except:
        pass
    return details

@st.cache_data(show_spinner=False)
def fetch_trailer(title):
    """Fetch first YouTube trailer link (no API key)."""
    try:
        query = title + " official trailer"
        url = f"https://www.youtube.com/results?search_query={query.replace(' ', '+')}"
        response = requests.get(url, timeout=5).text
        match = re.search(r'"videoId":"(.*?)"', response)
        if match:
            video_id = match.group(1)
            return f"https://www.youtube.com/watch?v={video_id}"
    except:
        pass
    return None

def recommend(movie):
    movie_index = movies[movies['title'] == movie].index[0]
    distances = similarity[movie_index]
    movies_list = sorted(list(enumerate(distances)), reverse=True, key=lambda x: x[1])[1:RECOMMEND_COUNT+1]

    recommended_movies = [movies.iloc[i[0]].title for i in movies_list]
    movie_ids = [movies.iloc[i[0]].movie_id for i in movies_list]

    with ThreadPoolExecutor() as executor:
        recommended_movies_posters = list(executor.map(fetch_poster, movie_ids))

    return recommended_movies, recommended_movies_posters

# ------------------- Load Data -------------------
movies_dict = pickle.load(open('movies_dict.pkl','rb'))
movies = pd.DataFrame(movies_dict)
similarity = pickle.load(open('similarity.pkl','rb'))

# ------------------- Streamlit UI -------------------
st.set_page_config(page_title="Movie Recommender", layout="wide")
st.markdown("## 🎬 Movie Recommender System")
st.write("Select a movie and get recommendations instantly!")

selected_movie_name = st.selectbox(
    'Search / Select a movie',
    movies['title'].values
)

# ------------------- Recommend Button -------------------
if st.button('Recommend'):
    selected_movie_id = movies[movies['title'] == selected_movie_name].iloc[0].movie_id
    selected_details = fetch_movie_details(selected_movie_id)
    trailer_url = fetch_trailer(selected_details["title"])

    # Display selected movie
    st.markdown("### Because you watched:")
    col1, col2 = st.columns([1, 2])
    with col1:
        st.image(selected_details["poster"], use_container_width=True)
    with col2:
        st.subheader(selected_details["title"])
        st.write(f"⭐ **Rating:** {selected_details['rating']}")
        st.write(f"📅 **Release Date:** {selected_details['release_date']}")
        st.write("**Overview:**")
        st.write(selected_details["overview"])
        if trailer_url:
            st.markdown(f"[▶ Watch Trailer]({trailer_url})", unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("### Recommended for you:")

    names, posters = recommend(selected_movie_name)

    # Hover animation
    st.markdown("""
        <style>
        .movie-poster:hover {
            transform: translateY(-10px);
            transition: 0.3s ease-in-out;
            cursor: pointer;
        }
        .movie-poster {
            border-radius: 10px;
            transition: 0.3s;
        }
        </style>
    """, unsafe_allow_html=True)

    cols = st.columns(RECOMMEND_COUNT)
    for idx, col in enumerate(cols):
        with col:
            st.markdown(
                f"<img src='{posters[idx]}' class='movie-poster' style='width:100%;'>",
                unsafe_allow_html=True
            )
            st.markdown(f"**{names[idx]}**")
            details = fetch_movie_details(movies[movies['title'] == names[idx]].iloc[0].movie_id)
            st.write(f"⭐ {details['rating']}")
            trailer = fetch_trailer(details["title"])
            if trailer:
                st.markdown(f"[▶ Trailer]({trailer})", unsafe_allow_html=True)
            with st.expander("More info"):
                st.write(details["overview"])
                st.write(f"📅 Release: {details['release_date']}")






















