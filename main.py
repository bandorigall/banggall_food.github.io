import csv
import json
import os

# === 설정 ===
input_csv = 'data.csv'
output_html = 'index.html'
# ============

def generate_html(csv_file, output_file):
    data = []
    
    if not os.path.exists(csv_file):
        print(f"오류: '{csv_file}' 파일을 찾을 수 없습니다. 같은 폴더에 위치시켜 주세요.")
        return

    try:
        with open(csv_file, 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            for row in reader:
                # 좌표 처리
                coords_str = row.get('좌표', '').replace('"', '').strip()
                lat, lng = None, None
                if coords_str:
                    coords = coords_str.split(',')
                    if len(coords) == 2:
                        try:
                            lat = float(coords[0].strip())
                            lng = float(coords[1].strip())
                        except ValueError:
                            pass
                
                # 구역 이름 변환
                area = row.get('구역', '').strip()
                if area == '홍대':
                    area = '서울_홍대'
                elif area == '서면':
                    area = '부산_서면'
                
                data.append({
                    'area': area,
                    'name': row.get('이름', '').strip(),
                    'google_map': row.get('구글맵링크', '').strip(),
                    'lat': lat,
                    'lng': lng,
                    'note': row.get('비고', '').strip()
                })
                
    except Exception as e:
        print(f"CSV 파일 읽기 오류: {e}")
        return

    if not data:
         print("오류: 데이터가 비어있습니다. CSV 파일을 확인해주세요.")
         return


    # HTML 템플릿 생성
    html_content = f"""
    <!DOCTYPE html>
    <html lang="ko">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
        <title>방붕 맛집 지도</title>
        <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" integrity="sha256-p4NxAoJBhIIN+hmNHrzRCf9tD/miZyoHS5obTRR9BMY=" crossorigin=""/>
        <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js" integrity="sha256-20nQCchB9co0qIjJZRGuk2/Z9VM+kNiyxNV1lvTlZBo=" crossorigin=""></script>
        
        <style>
            /* 기본 스타일 */
            body, html {{ margin: 0; padding: 0; height: 100%; font-family: 'Pretendard', 'Malgun Gothic', sans-serif; background-color: #FFFDF9; color: #4A3F35; overflow: hidden; }}
            body {{ display: flex; flex-direction: column; }}
            
            /* 헤더 */
            header {{ background-color: #FF9F43; padding: 12px 15px; display: flex; justify-content: space-between; align-items: center; color: white; box-shadow: 0 2px 5px rgba(0,0,0,0.1); flex-shrink: 0; z-index: 1000; }}
            h1 {{ margin: 0; font-size: 1.3rem; font-weight: 700; }}
            .dc-link {{ color: white; text-decoration: none; font-weight: 600; background-color: rgba(255,255,255,0.2); padding: 6px 10px; border-radius: 6px; transition: background 0.2s; font-size: 0.8rem; white-space: nowrap; }}
            .dc-link:hover {{ background-color: rgba(255,255,255,0.3); }}
            
            /* 메인 컨테이너 (지도 + 사이드바) */
            #main-container {{ display: flex; flex: 1; overflow: hidden; position: relative; }}
            
            /* 사이드바 (리스트 영역) */
            #sidebar {{ width: 420px; min-width: 420px; background-color: #FAFAFA; border-right: 1px solid #E0E0E0; display: flex; flex-direction: column; overflow: hidden; z-index: 900; }}
            
            /* 필터 버튼 영역 */
            #filters {{ padding: 10px; border-bottom: 1px solid #E0E0E0; background-color: #fff; display: flex; flex-wrap: wrap; gap: 6px; flex-shrink: 0; }}
            .filter-btn {{ padding: 6px 12px; border: 1px solid #ddd; border-radius: 20px; background-color: #f8f8f8; color: #666; cursor: pointer; font-weight: 600; transition: all 0.2s; font-size: 0.85rem; }}
            .filter-btn:hover {{ background-color: #eee; }}
            .filter-btn.active {{ background-color: #FF9F43; color: white; border-color: #FF9F43; box-shadow: 0 2px 4px rgba(255, 159, 67, 0.3); }}
            
            /* 리스트 컨테이너 (스크롤 영역) */
            #list-container {{ flex: 1; overflow-y: auto; padding: 10px; -webkit-overflow-scrolling: touch; background-color: #f4f4f4; }}
            
            /* 개별 리스트 아이템 */
            .list-item {{ background: white; border: 1px solid #E8E8E8; padding: 15px; margin-bottom: 10px; border-radius: 10px; cursor: pointer; transition: transform 0.1s, box-shadow 0.1s; }}
            .list-item:active {{ transform: scale(0.99); }}
            .list-item.active {{ border: 2px solid #FF9F43; background-color: #FFF8F0; box-shadow: 0 4px 8px rgba(255, 159, 67, 0.15); }}
            .item-header {{ display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 5px; }}
            .item-name {{ font-size: 1.1rem; font-weight: 700; color: #E67E22; }}
            .item-area-badge {{ font-size: 0.75rem; background-color: #eee; padding: 3px 6px; border-radius: 4px; color: #666; }}
            .item-note {{ font-size: 0.9rem; color: #666; margin-bottom: 12px; line-height: 1.4; word-break: break-word; }}
            
            /* 버튼 그룹 */
            .btn-group {{ display: flex; gap: 6px; flex-wrap: wrap; margin-top: auto; }}
            .btn {{ padding: 6px 10px; font-size: 0.8rem; text-decoration: none; color: white; border-radius: 5px; font-weight: 600; display: inline-flex; align-items: center; transition: opacity 0.2s; }}
            .btn:hover {{ opacity: 0.9; }}
            .btn-google {{ background-color: #4285F4; }}
            .btn-naver {{ background-color: #03C75A; }}
            .btn-kakao {{ background-color: #FEE500; color: #000; }}
            
            /* 지도 영역 */
            #map {{ flex: 1; height: 100%; background-color: #f0f0f0; }}
            
            /* 푸터 */
            footer {{ text-align: center; padding: 8px; background-color: #34495e; color: #bdc3c7; font-size: 0.75rem; flex-shrink: 0; }}
            footer a {{ color: #bdc3c7; text-decoration: none; }}

            /* ========== 모바일 반응형 스타일 (스크롤 버그 완벽 수정) ========== */
            @media (max-width: 768px) {{
                /* 모바일 브라우저 하단바 높이까지 정확히 계산(dvh)하여 스크롤 짤림 방지 */
                body, html {{ height: 100%; height: 100dvh; overflow: hidden; }} 
                
                h1 {{ font-size: 1.1rem; }}
                .dc-link {{ font-size: 0.75rem; padding: 5px 8px; }}
                header {{ padding: 10px; flex-shrink: 0; }}
                footer {{ flex-shrink: 0; }}
                
                #main-container {{ flex-direction: column; flex: 1; overflow: hidden; }}
                
                /* 모바일: 지도 상단 (화면의 40% 차지) */
                #map {{ width: 100%; height: 40vh; flex: none; order: 1; border-bottom: 1px solid #ddd; }}
                
                /* 모바일: 사이드바 하단 (나머지 화면 꽉 채우고, 자체 스크롤 생성) */
                #sidebar {{ width: 100%; min-width: 100%; flex: 1; order: 2; border-right: none; display: flex; flex-direction: column; overflow: hidden; }}
                
                /* 모바일: 이 영역 안에서만 스크롤이 시원하게 내려가도록 처리 */
                #list-container {{ flex: 1; overflow-y: auto; padding-bottom: 30px; -webkit-overflow-scrolling: touch; }}
                
                .leaflet-popup-content {{ margin: 10px; max-width: 260px; }}
                .leaflet-popup-tip-container {{ display: none; }}
            }}
        </style>
    </head>
    <body>
        <header>
            <h1>방붕 맛집 지도</h1>
            <a href="https://gall.dcinside.com/mgallery/board/lists?id=bang_dream" target="_blank" class="dc-link">뱅드림 갤러리 가기</a>
        </header>
        
        <div id="main-container">
            <div id="sidebar">
                <div id="filters">
                    </div>
                <div id="list-container">
                    </div>
            </div>
            
            <div id="map"></div>
        </div>
        
        <footer>
            made by Bangbung Kim | <a href="https://gall.dcinside.com/mgallery/board/lists?id=bang_dream" target="_blank">DCInside BangDream Gallery</a>
        </footer>

        <script>
            const data = {json.dumps(data, ensure_ascii=False)};
            
            let map;
            let markers = [];
            let currentArea = 'ALL';
            let isMobile = window.innerWidth <= 768;

            window.addEventListener('resize', () => {{
                isMobile = window.innerWidth <= 768;
            }});

            function initMap() {{
                map = L.map('map', {{ zoomControl: false }}).setView([36.5, 127.5], 7);
                L.control.zoom({{ position: 'bottomright' }}).addTo(map);

                L.tileLayer('https://{{s}}.tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png', {{
                    attribution: '© OpenStreetMap contributors',
                    opacity: 0.7, 
                    maxZoom: 19
                }}).addTo(map);
            }}

            function populateFilters() {{
                const container = document.getElementById('filters');
                const areas = ['ALL', ...new Set(data.map(item => item.area))].filter(Boolean).sort();
                
                areas.forEach(area => {{
                    const btn = document.createElement('button');
                    btn.className = 'filter-btn' + (area === 'ALL' ? ' active' : '');
                    btn.textContent = area === 'ALL' ? '전체 보기' : area.replace('_', ' ');
                    
                    btn.onclick = () => {{
                        document.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
                        btn.classList.add('active');
                        
                        currentArea = area;
                        renderList();
                        renderMarkers();
                    }};
                    container.appendChild(btn);
                }});
            }}

            function getButtonsHtml(item) {{
                const query = encodeURIComponent(item.area.replace('_', ' ') + ' ' + item.name);
                let html = '<div class="btn-group">';
                
                if (item.google_map) {{
                    html += `<a href="${{item.google_map}}" target="_blank" class="btn btn-google">Google</a>`;
                }} else {{
                    html += `<a href="https://www.google.com/maps/search/?api=1&query=${{query}}" target="_blank" class="btn btn-google">Google 검색</a>`;
                }}
                
                html += `<a href="https://map.naver.com/p/search/${{query}}" target="_blank" class="btn btn-naver">Naver</a>`;
                html += `<a href="https://map.kakao.com/link/search/${{query}}" target="_blank" class="btn btn-kakao">Kakao</a>`;
                html += '</div>';
                return html;
            }}

            function renderList() {{
                const container = document.getElementById('list-container');
                container.innerHTML = ''; 
                const filteredData = currentArea === 'ALL' ? data : data.filter(d => d.area === currentArea);
                
                if (filteredData.length === 0) {{
                    container.innerHTML = '<div style="text-align:center; padding:20px; color:#888;">해당 구역에 맛집 데이터가 없습니다.</div>';
                    return;
                }}

                filteredData.forEach((item) => {{
                    const dataIndex = data.indexOf(item); 
                    const div = document.createElement('div');
                    div.className = 'list-item';
                    div.id = `item-${{dataIndex}}`;
                    
                    div.innerHTML = `
                        <div class="item-header">
                            <div class="item-name">${{item.name}}</div>
                            <span class="item-area-badge">${{item.area.replace('_', ' ')}}</span>
                        </div>
                        <div class="item-note">${{item.note || '(비고 없음)'}}</div>
                        ${{getButtonsHtml(item)}}
                    `;
                    
                    div.onclick = () => {{
                        highlightItem(dataIndex);
                        
                        if (item.lat && item.lng) {{
                            map.flyTo([item.lat, item.lng], 16, {{ duration: 0.5 }});
                            const targetMarker = markers.find(m => m.itemIndex === dataIndex);
                            if (targetMarker) {{
                                targetMarker.marker.openPopup();
                            }}
                            
                            if (isMobile) {{
                                document.getElementById('map').scrollIntoView({{ behavior: 'smooth' }});
                            }}
                        }}
                    }};
                    container.appendChild(div);
                }});
            }}

            function renderMarkers() {{
                markers.forEach(m => map.removeLayer(m.marker));
                markers = [];
                
                const filteredData = currentArea === 'ALL' ? data : data.filter(d => d.area === currentArea);
                const bounds = L.latLngBounds();
                let hasValidCoords = false;

                filteredData.forEach((item) => {{
                    const dataIndex = data.indexOf(item);
                    if (item.lat !== null && item.lng !== null) {{
                        hasValidCoords = true;
                        const marker = L.marker([item.lat, item.lng]).addTo(map);
                        
                        marker.bindTooltip(item.name, {{ direction: 'top', offset: [0, -20] }});
                        
                        const popupContent = `
                            <div style="min-width: 200px;">
                                <h3 style="margin:0 0 5px 0; color:#E67E22;">${{item.name}}</h3>
                                <p style="margin:0 0 10px 0; font-size:0.9rem; color:#666;">${{item.note || ''}}</p>
                                ${{getButtonsHtml(item)}}
                            </div>
                        `;
                        marker.bindPopup(popupContent);

                        marker.on('click', () => {{
                            highlightItem(dataIndex);
                            const listItem = document.getElementById(`item-${{dataIndex}}`);
                            if (listItem) {{
                                listItem.scrollIntoView({{ behavior: 'smooth', block: isMobile ? 'start' : 'center' }});
                            }}
                        }});
                        
                        markers.push({{ marker, itemIndex: dataIndex }});
                        bounds.extend([item.lat, item.lng]);
                    }}
                }});

                if (hasValidCoords) {{
                    map.fitBounds(bounds, {{ padding: [50, 50], maxZoom: 17 }});
                }}
            }}

            function highlightItem(index) {{
                document.querySelectorAll('.list-item').forEach(el => el.classList.remove('active'));
                const target = document.getElementById(`item-${{index}}`);
                if (target) {{
                    target.classList.add('active');
                }}
            }}

            initMap();
            populateFilters();
            renderList();
            renderMarkers();

        </script>
    </body>
    </html>
    """

    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html_content)

    print(f"성공! '{output_file}' 파일이 생성되었습니다.")
    print("웹 브라우저로 열어서 확인해보세요.")

if __name__ == "__main__":
    generate_html(input_csv, output_html)