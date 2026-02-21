import csv
import json

def generate_html(csv_file, output_file):
    data = []
    
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

    html_content = f"""
    <!DOCTYPE html>
    <html lang="ko">
    <head>
        <meta charset="UTF-8">
        <title>방붕 맛집 지도</title>
        <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
        <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
        <style>
            body {{ margin: 0; font-family: 'Malgun Gothic', sans-serif; background-color: #FFFDF9; color: #4A3F35; display: flex; flex-direction: column; height: 100vh; }}
            header {{ background-color: #FFB347; padding: 15px 20px; display: flex; justify-content: space-between; align-items: center; color: white; box-shadow: 0 2px 5px rgba(0,0,0,0.1); z-index: 1000; }}
            h1 {{ margin: 0; font-size: 24px; text-shadow: 1px 1px 2px rgba(0,0,0,0.2); }}
            .dc-link {{ color: white; text-decoration: none; font-weight: bold; background-color: rgba(255,255,255,0.2); padding: 5px 10px; border-radius: 5px; transition: background 0.2s; }}
            .dc-link:hover {{ background-color: rgba(255,255,255,0.4); }}
            #main-container {{ display: flex; flex: 1; overflow: hidden; }}
            #sidebar {{ width: 450px; min-width: 450px; background-color: #FAFAFA; border-right: 1px solid #E0E0E0; display: flex; flex-direction: column; }}
            #filters {{ padding: 15px; border-bottom: 1px solid #E0E0E0; background-color: white; display: flex; flex-wrap: wrap; gap: 8px; }}
            .filter-btn {{ padding: 8px 15px; border: none; border-radius: 20px; background-color: #EEEEEE; color: #555; cursor: pointer; font-weight: bold; transition: all 0.2s; font-size: 14px; }}
            .filter-btn:hover {{ background-color: #E0E0E0; }}
            .filter-btn.active {{ background-color: #FFB347; color: white; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
            #list-container {{ flex: 1; overflow-y: auto; padding: 10px; }}
            .list-item {{ background: white; border: 1px solid #E8E8E8; padding: 15px; margin-bottom: 10px; border-radius: 8px; cursor: pointer; transition: all 0.2s; box-shadow: 0 1px 3px rgba(0,0,0,0.05); }}
            .list-item:hover {{ transform: translateY(-2px); box-shadow: 0 4px 6px rgba(0,0,0,0.1); border-color: #FFB347; }}
            .list-item.active {{ border: 2px solid #FFB347; background-color: #FFF9F0; }}
            .item-name {{ font-size: 18px; font-weight: bold; margin-bottom: 5px; color: #D35400; }}
            .item-note {{ font-size: 13px; color: #7F8C8D; margin-bottom: 10px; line-height: 1.4; }}
            .btn-group {{ display: flex; gap: 5px; flex-wrap: wrap; }}
            .btn {{ padding: 5px 10px; font-size: 12px; text-decoration: none; color: white; border-radius: 4px; display: inline-block; font-weight: bold; }}
            .btn-google {{ background-color: #4285F4; }}
            .btn-naver {{ background-color: #03C75A; }}
            .btn-kakao {{ background-color: #FEE500; color: #000; }}
            #map {{ flex: 1; }}
            footer {{ text-align: center; padding: 10px; background-color: #333; color: #FFF; font-size: 12px; }}

            /* 모바일 반응형 CSS 추가 */
            @media (max-width: 768px) {{
                #main-container {{ flex-direction: column; }}
                #sidebar {{ width: 100%; min-width: 100%; flex: 1; order: 2; border-right: none; }}
                #map {{ width: 100%; height: 45vh; flex: none; order: 1; border-bottom: 2px solid #E0E0E0; z-index: 10; }}
            }}
        </style>
    </head>
    <body>
        <header>
            <h1>방붕 맛집 지도</h1>
            <a href="https://gall.dcinside.com/mgallery/board/lists?id=bang_dream" target="_blank" class="dc-link">디시인사이드 뱅드림 마이너 갤러리</a>
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
                    attribution: '© OpenStreetMap contributors'
                }}).addTo(map);
            }}

            function populateFilters() {{
                const container = document.getElementById('filters');
                const areas = ['ALL', ...new Set(data.map(item => item.area))].filter(Boolean);
                
                areas.forEach(area => {{
                    const btn = document.createElement('button');
                    btn.className = 'filter-btn';
                    
                    if (area === 'ALL') {{
                        btn.textContent = '전체 구역';
                        btn.classList.add('active');
                    }} else {{
                        btn.textContent = area;
                    }}
                    
                    btn.addEventListener('click', () => {{
                        document.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
                        btn.classList.add('active');
                        currentArea = area;
                        renderList();
                        renderMarkers();
                    }});
                    container.appendChild(btn);
                }});
            }}

            function getButtonsHtml(item) {{
                let html = '<div class="btn-group">';
                if (item.google_map) {{
                    html += `<a href="${{item.google_map}}" target="_blank" class="btn btn-google">Google Map</a>`;
                }}
                html += `<a href="https://map.naver.com/p/search/${{encodeURIComponent(item.area + ' ' + item.name)}}" target="_blank" class="btn btn-naver">Naver Map</a>`;
                html += `<a href="https://map.kakao.com/?q=${{encodeURIComponent(item.area + ' ' + item.name)}}" target="_blank" class="btn btn-kakao">Kakao Map</a>`;
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
                    div.addEventListener('click', () => {{
                        highlightItem(dataIndex);
                        if (item.lat && item.lng) {{
                            map.setView([item.lat, item.lng], 17);
                            markers.forEach(m => {{
                                if(m.itemIndex === dataIndex) m.marker.openPopup();
                            }});
                        }}
                    }});
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
                    if (item.lat && item.lng) {{
                        hasValidCoords = true;
                        const marker = L.marker([item.lat, item.lng]).addTo(map);
                        
                        marker.bindTooltip(item.name);
                        
                        marker.bindPopup(`
                            <strong>${{item.name}}</strong><br>
                            <span style="font-size:12px; color:#666;">${{item.note}}</span><br><br>
                            ${{getButtonsHtml(item)}}
                        `);
                        marker.on('click', () => {{
                            highlightItem(dataIndex);
                            const listItem = document.getElementById(`item-${{dataIndex}}`);
                            if(listItem) listItem.scrollIntoView({{ behavior: 'smooth', block: 'center' }});
                        }});
                        markers.push({{ marker: marker, itemIndex: dataIndex }});
                        bounds.extend([item.lat, item.lng]);
                    }}
                }});

                if (hasValidCoords) {{
                    map.fitBounds(bounds, {{ padding: [50, 50] }});
                }}
            }}

            function highlightItem(index) {{
                document.querySelectorAll('.list-item').forEach(el => el.classList.remove('active'));
                const target = document.getElementById(`item-${{index}}`);
                if (target) target.classList.add('active');
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

    print(f"작업 완료! {{output_file}} 파일 확장자 저장 완료!")

if __name__ == "__main__":
    generate_html('data.csv', 'index.html')