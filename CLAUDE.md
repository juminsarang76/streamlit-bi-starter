# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Streamlit-based BI dashboard starter application that displays sample e-commerce data (orders and users). The project uses Python with Streamlit for the web interface and Pandas for data manipulation.

## Architecture

- **Main Application**: `Home.py` - Multi-page Streamlit application that loads and displays CSV data
- **Pages**: `pages/` directory contains additional pages (`About_Us.py`)
- **Data**: `sample_data/` directory contains CSV files with e-commerce data
- **Local Processing**: `local/` directory contains data processing scripts
- **Dependencies**: Managed via `pyproject.toml` using uv as the package manager

## Key Components

- **Data Loading**: Uses `@st.cache_data` decorator for efficient CSV loading
- **UI Structure**: Wide layout with data tables displaying the first 10 rows of each dataset
- **Multi-page Support**: Streamlit's native multi-page architecture with pages in `pages/` directory
- **Sample Data**: 
  - `orders.csv`: E-commerce order data with status, timestamps, and item counts
  - `users.csv`: User profile data with demographics and geographic information
  - `order_items.csv`: Individual order items data
  - `products.csv`: Product information data

## Development Commands

### Setup and Installation
```bash
uv sync
```

### Running the Application
```bash
uv run streamlit run Home.py
```

### Package Management
```bash
uv add package-name
uv sync
```

## Development Notes

- The application uses Python >=3.11 as specified in pyproject.toml
- Streamlit configuration is set to wide layout mode
- Data caching is implemented for performance with `@st.cache_data`
- Multi-page architecture allows for easy expansion of functionality
- Dependencies include Plotly for enhanced data visualization capabilities
- No testing framework is currently configured
- No linting or formatting tools are configured in the project

---

# 정보 수집 에이전트 지시

매 실행 시마다 다음 정보를 수집하고, reports/{오늘의 날짜}.md 에 추기해 주세요.
파일이 이미 존재하는 경우 덮어쓰기가 아닌 추가(append)할 것.

## 수집할 정보

### 기술 정보
- Velog 트렌드 (상위 5개): https://velog.io/
- 요즘IT 인기 기사 (상위 5개): https://yozm.wishket.com/
- GitHub Trending (당일): https://github.com/trending

### 경제 정보
- 코스피/코스닥 지수 (현재값·전일 대비)
- USD/KRW 환율 (현재값)
- 주요 마켓 뉴스 (3건 정도)

## 출력 포맷

각 섹션에 「취득 시각」을 기재할 것.
기사 제목, 요약, URL을 세트로 출력할 것.
경제 뉴스는 1행 요약으로 기재할 것.

## md file viewer 업데이트
이미 만들어져 있으면 업데이트만
html로 md viewer를 만들어서 업데이트
왼쪽은 view, 오른쪽은 리스트, 리스트 클릭하면 view가 보일 수 있도록
