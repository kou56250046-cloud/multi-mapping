-- 開発用シードデータ（東京・神奈川の有名な自然スポット）

INSERT INTO spots (id, name, description, category, latitude, longitude, nickname) VALUES
  ('seed-001', '等々力渓谷', '東京23区内唯一の渓谷。川の音が聞こえて瞑想に最適。', 'meditation', 35.6063, 139.6517, '管理人'),
  ('seed-002', '高尾山', 'ハイキングコースが豊富。599mの低山だが自然豊か。', 'walking', 35.6256, 139.2436, '管理人'),
  ('seed-003', '昭和記念公園', '広大な敷地でピクニックやスポーツが楽しめる。', 'sports', 35.7079, 139.4083, '管理人'),
  ('seed-004', '城ヶ島', '神奈川県の海辺。岩礁と海が美しい穴場スポット。', 'hidden_gem', 35.1369, 139.6189, '管理人'),
  ('seed-005', '丹沢大山', '関東屈指の自然。沢沿いで川の音が心地よい。', 'waterside', 35.4408, 139.2317, '管理人'),
  ('seed-006', '払沢の滝', '日本の滝百選にも選ばれた美しい滝。', 'waterfall', 35.7558, 139.1442, '管理人'),
  ('seed-007', '城南島海浜公園', 'BBQ施設あり。飛行機の離着陸も見える。', 'bbq', 35.5867, 139.7689, '管理人');

INSERT INTO spot_tags (spot_id, tag) VALUES
  ('seed-001', 'few_people'),
  ('seed-001', 'shade'),
  ('seed-002', 'toilet'),
  ('seed-002', 'parking'),
  ('seed-003', 'bbq_ok'),
  ('seed-003', 'parking'),
  ('seed-003', 'toilet'),
  ('seed-003', 'water'),
  ('seed-004', 'few_people'),
  ('seed-005', 'few_people'),
  ('seed-005', 'shade'),
  ('seed-007', 'bbq_ok'),
  ('seed-007', 'parking'),
  ('seed-007', 'toilet'),
  ('seed-007', 'water');
