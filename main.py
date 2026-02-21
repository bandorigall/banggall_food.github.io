import csv
import json

def generate_html(csv_file, output_file):
    data = []
    
    # CSV 데이터 읽기
    with open(csv_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            coords = row['좌표'].replace('"', '').split(',')
            lat, lng = None, None
            if len(coords) == 2:
                try:
                    lat = float(coords[0].strip())
                    lng = float(coords[1].strip())
                except ValueError:
                    pass
            
            # 구역 이름 변환 (홍대 -> 서울_홍대, 서면 -> 부산_서면)
            area = row['구역'].strip()
            if area == '홍대':
                area = '서울_홍대'
            elif area == '서면':
                area = '부산_서면'
            
            data.append({
                'area': area,
                'name': row['이름'].strip(),
                'google_map': row['구글맵링크'].strip(),
                'lat': lat,
                'lng': lng,
                'note': row['비고'].strip()
            })

    # HTML 템플릿 생성
    html_content = f"""
    <!DOCTYPE html>
    <html lang="ko">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
        <title>방붕 맛집 지도</title>
        <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
        <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
        <style>
            body {{ margin: 0; font-family: 'Malgun Gothic', sans-serif; background-color: #FFFDF9; color: #4A3F35; display: flex; flex-direction: column; height: 100vh; overflow: hidden; }}
            header {{ background-color: #FFB347; padding: 15px 20px; display: flex; justify-content: space-between; align-items: center; color: white; box-shadow: 0 2px 5px rgba(0,0,0,0.1); z-index: 1000; flex-shrink: 0; }}
            h1 {{ margin: 0; font-size: 20px; text-shadow: 1px 1px 2px rgba(0,0,0,0.2); }}
            .dc-link {{ color: white; text-decoration: none; font-weight: bold; background-color: rgba(255,255,255,0.2); padding: 5px 10px; border-radius: 5px; transition: background 0.2s; font-size: 12px; }}
            
            #main-container {{ display: flex; flex: 1; overflow: hidden; }}
            #sidebar {{ width: 450px; min-width: 450px; background-color: #FAFAFA; border-right: 1px solid #E0E0E0; display: flex; flex-direction: column; overflow: hidden; }}
            #filters {{ padding: 12px; border-bottom: 1px solid #E0E0E0; background-color: white; display: flex; flex-wrap: wrap; gap: 6px; flex-shrink: 0; }}
            .filter-btn {{ padding: 6px 12px; border: none; border-radius: 15px; background-color: #EEEEEE; color: #555; cursor: pointer; font-weight: bold; transition: all 0.2s; font-size: 13px; }}
            .filter-btn.active {{ background-color: #FFB347; color: white; }}
            
            #list-container {{ flex: 1; overflow-y: auto; padding: 10px; -webkit-overflow-scrolling: touch; }}
            .list-item {{ background: white; border: 1px solid #E8E8E8; padding: 15px; margin-bottom: 10px; border-radius: 8px; cursor: pointer; }}
            .list-item.active {{ border: 2px solid #FFB347; background-color: #FFF9F0; }}
            .item-name {{ font-size: 17px; font-weight: bold; margin-bottom: 4px; color: #D35400; }}
            .item-note {{ font-size: 13px; color: #7F8C8D; margin-bottom: 10px; }}
            
            .btn-group {{ display: flex; gap: 4px; flex-wrap: wrap; }}
            .btn {{ padding: 4px 8px; font-size: 11px; text-decoration: none; color: white; border-radius: 4px; font-weight: bold; }}
            .btn-google {{ background-color: #4285F4; }}
            .btn-naver {{ background-color: #03C75A; }}
            .btn-kakao {{ background-color: #FEE500; color: #000; }}
            
            #map {{ flex: 1; z-index: 1; }}
            footer {{ text-align: center; padding: 8px; background-color: #333; color: #FFF; font-size: 11px; flex-shrink: 0; }}

            /* 모바일 반응형 핵심 수정 */
            @media (max-width: 768px) {{
                #main-container {{ flex-direction: column; }}
                #map {{ width: 100%; height: 40vh; flex: none; order: 1; border-bottom: 2px solid #E0E0E0; }}
                #sidebar {{ width: 100%; min-width: 100%; height: 60vh; flex: 1; order: 2; border-right: none; }}
                h1 {{ font-size: 18px; }}
                .dc-link {{ font-size: 10px; padding: 4px 8px; }}
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
                <div id="filters"></div>
                <div id="list-container"></div>
            </div>
            <div id="map"></div>
        </div>
        <footer>
            made by Bangbung Kim
        </footer>

        <script>
            const data = {json.dumps(data, ensure_ascii=False)};
            let map;
            let markers = [];
            let currentArea = 'ALL';

            function initMap() {{
                map = L.map('map').setView([36.5, 127.5], 7);
                L.tileLayer('https://{{s}}.tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png', {{
                    attribution: '© OSM'
                }}).addTo(map);
            }}

            function populateFilters() {{
                const container = document.getElementById('filters');
                const areas = ['ALL', ...new Set(data.map(item => item.area))].filter(Boolean);
                
                areas.forEach(area => {{
                    const btn = document.createElement('button');
                    btn.className = 'filter-btn' + (area === 'ALL' ? ' active' : '');
                    btn.textContent = area === 'ALL' ? '전체' : area;
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
                let html = '<div class="btn-group">';
                if (item.google_map) html += `<a href="${{item.google_map}}" target="_blank" class="btn btn-google">Google</a>`;
                html += `<a href="https://map.naver.com/p/search/${{encodeURIComponent(item.area + ' ' + item.name)}}" target="_blank" class="btn btn-naver">Naver</a>`;
                html += `<a href="https://map.kakao.com/?q=${{encodeURIComponent(item.area + ' ' + item.name)}}" target="_blank" class="btn btn-kakao">Kakao</a>`;
                html += '</div>';
                return html;
            }}

            function renderList() {{
                const container = document.getElementById('list-container');
                container.innerHTML = '';
                const filteredData = currentArea === 'ALL' ? data : data.filter(d => d.area === currentArea);
                
                filteredData.forEach((item) => {{
                    const dataIndex = data.indexOf(item);
                    const div = document.createElement('div');
                    div.className = 'list-item';
                    div.id = `item-${{dataIndex}}`;
                    div.innerHTML = `
                        <div class="item-name">${{item.name}}</div>
                        <div class="item-note">${{item.note || ''}}</div>
                        ${{getButtonsHtml(item)}}
                    `;
                    div.onclick = () => {{
                        highlightItem(dataIndex);
                        if (item.lat && item.lng) {{
                            map.setView([item.lat, item.lng], 16);
                            markers.find(m => m.itemIndex === dataIndex)?.marker.openPopup();
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
                let hasValid = false;

                filteredData.forEach((item) => {{
                    const dataIndex = data.indexOf(item);
                    if (item.lat && item.lng) {{
                        hasValid = true;
                        const marker = L.marker([item.lat, item.lng]).addTo(map);
                        marker.bindTooltip(item.name);
                        marker.bindPopup(`<strong>${{item.name}}</strong><br>${{getButtonsHtml(item)}}`);
                        marker.on('click', () => {{
                            highlightItem(dataIndex);
                            const el = document.getElementById(`item-${{dataIndex}}`);
                            if(el) el.scrollIntoView({{ behavior: 'smooth', block: 'center' }});
                        }});
                        markers.push({{ marker, itemIndex: dataIndex }});
                        bounds.extend([item.lat, item.lng]);
                    }}
                }});
                if (hasValid) map.fitBounds(bounds, {{ padding: [30, 30] }});
            }}

            function highlightItem(index) {{
                document.querySelectorAll('.list-item').forEach(el => el.classList.remove('active'));
                document.getElementById(`item-${{index}}`)?.classList.add('active');
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
    print(f"index.html 생성 완료!")

if __name__ == "__main__":
    generate_html('data.csv', 'index.html')