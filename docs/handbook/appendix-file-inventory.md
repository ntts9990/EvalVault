# 파일 인벤토리 (File Inventory)

> 이 문서는 프로젝트 교과서 작성을 위한 전체 파일 인벤토리입니다.
> Task 3(전수 정독)에서 Evidence, 요약, 외부공개 여부 등 상세 정보가 추가됩니다.

## 1. Inventory Summary

| 항목 | 값 |
|------|-----|
| **스냅샷 기준일시** | 2026-01-28 17:43:45 |
| **HEAD 커밋** | `d02611bda80b...` |
| **Raw List 총 파일 수** | 1784 |
| **포함 파일 수** | 1117 |
| **제외 파일 수** | 667 |
| **제외 디렉터리 수** | 82 |

## 2. Raw List

총 **1784**개 파일 (정렬된 경로 목록)

<details>
<summary>전체 파일 목록 펼치기 (클릭)</summary>

```
./.claude/settings.local.json
./.dockerignore
./.env.example
./.github/workflows/ci.yml
./.github/workflows/regression-gate.yml
./.github/workflows/release.yml
./.github/workflows/stale.yml
./.gitignore
./.pre-commit-config.yaml
./.python-version
./.sisyphus/boulder.json
./.sisyphus/drafts/offline-docker-image-plan.md
./.sisyphus/notepads/offline-docker/decisions.md
./.sisyphus/notepads/offline-docker/issues.md
./.sisyphus/notepads/offline-docker/learnings.md
./.sisyphus/notepads/offline-docker/problems.md
./.sisyphus/notepads/p0-settings/worklog.md
./.sisyphus/notepads/p1-webui/worklog.md
./.sisyphus/notepads/p2-observability/worklog.md
./.sisyphus/notepads/p3-performance/worklog.md
./.sisyphus/notepads/p7-regression/worklog.md
./.sisyphus/notepads/p9-offline/worklog.md
./.sisyphus/notepads/project-handbook/decisions.md
./.sisyphus/notepads/project-handbook/issues.md
./.sisyphus/notepads/project-handbook/learnings.md
./.sisyphus/notepads/project-handbook/problems.md
./.sisyphus/plans/project-handbook.md
./AGENTS.md
./CHANGELOG.md
./CLAUDE.md
./CODE_OF_CONDUCT.md
./CONTRIBUTING.md
./Dockerfile
./LICENSE.md
./README.en.md
./README.md
./SECURITY.md
./agent/README.md
./agent/agent.py
./agent/client.py
./agent/config.py
./agent/main.py
./agent/memory/README.md
./agent/memory/shared/decisions.md
./agent/memory/shared/dependencies.md
./agent/memory/templates/coordinator_guide.md
./agent/memory/templates/work_log_template.md
./agent/memory_integration.py
./agent/progress.py
./agent/prompts.py
./agent/prompts/app_spec.txt
./agent/prompts/baseline.txt
./agent/prompts/coding_prompt.md
./agent/prompts/existing_project_prompt.md
./agent/prompts/improvement/architecture_prompt.md
./agent/prompts/improvement/base_prompt.md
./agent/prompts/improvement/coordinator_prompt.md
./agent/prompts/improvement/observability_prompt.md
./agent/prompts/initializer_prompt.md
./agent/prompts/prompt_manifest.json
./agent/prompts/system.txt
./agent/requirements.txt
./agent/security.py
./config/domains/insurance/memory.yaml
./config/domains/insurance/terms_dictionary_en.json
./config/domains/insurance/terms_dictionary_ko.json
./config/methods.yaml
./config/models.yaml
./config/ragas_prompts_override.yaml
./config/regressions/ci.json
./config/regressions/default.json
./config/regressions/ux.json
./config/stage_metric_playbook.yaml
./config/stage_metric_thresholds.json
./data/cache/versioned_pdf/049ba246c8f52f8e657e74eaaa5338e1eaeba60d.json
./data/cache/versioned_pdf/04e07b7714eb2003c0cadb53b44f1347af33147c.json
./data/cache/versioned_pdf/0ebc412f6183011eff6c5c8f980fbd75803afec0.json
./data/cache/versioned_pdf/395aec80f8a047887302b6c5ebd6fa3ed6f3db56.json
./data/cache/versioned_pdf/42010a4f76c815efdd037a81517c6d37266ba009.json
./data/cache/versioned_pdf/52c7a3bf3b85f6b182deebf850a2afb85f175b71.json
./data/cache/versioned_pdf/74a8fd6e07c26fdc7a481f033a739af6f862ccc3.json
./data/cache/versioned_pdf/8417721918064cce86b4968d8d39c65e1b333b52.json
./data/cache/versioned_pdf/93f6df2df0a08503c899830fcd81cecb780fbe35.json
./data/cache/versioned_pdf/953faf21ee8abc6bf22bad3942b772310ee2e190.json
./data/cache/versioned_pdf/966d2e8bd1cba9bdabba4e1f6d0f20918770bbe4.json
./data/cache/versioned_pdf/97f30d96b6ef13e99a2d602cab55d578d40a99a8.json
./data/cache/versioned_pdf/98f19d1962e682ba3ae3bf699ce16b055795a220.json
./data/cache/versioned_pdf/cd2b2b985a159b4d7c6b63e0b87cc0391717666e.json
./data/cache/versioned_pdf/cf4ee9227919437d72f52b9c61fc0eb55d64a386.json
./data/cache/versioned_pdf/d0f351eaf1bd4192e25b9544e5623f0661627c25.json
./data/cache/versioned_pdf/d68cb665a21d569119a805b1942425e26e59f572.json
./data/cache/versioned_pdf/de9ef0c97fd0401dca998183c7e3bce18c5a163f.json
./data/cache/versioned_pdf/f35f04a19b38aaf8ce2aa7a9dd9596e96af0e9cf.json
./data/cache/versioned_pdf/fef39322cf49f48dbdf293f7fcbedbdefdb62696.json
./data/datasets/dummy_test_dataset.json
./data/datasets/insurance_qa_korean.csv
./data/datasets/insurance_qa_korean.json
./data/datasets/insurance_qa_korean_2.json
./data/datasets/insurance_qa_korean_3.json
./data/datasets/ragas_ko90_en10.json
./data/datasets/sample.json
./data/datasets/visualization_20q_cluster_map.csv
./data/datasets/visualization_20q_korean.json
./data/datasets/visualization_2q_cluster_map.csv
./data/datasets/visualization_2q_korean.json
./data/db/evalvault.db
./data/db/evalvault_memory.db
./data/db/evalvault_run_0019083a-ed7a-4448-b074-ee259013c671.xlsx
./data/db/evalvault_run_00ee0353-5544-44ca-b018-e0f0265f2867.xlsx
./data/db/evalvault_run_01ccc9fd-d670-4337-a2d5-a5cbff334916.xlsx
./data/db/evalvault_run_01da597b-aded-488a-8f58-877f373bc09f.xlsx
./data/db/evalvault_run_01ffa508-0a8f-4451-9249-c44666b337c6.xlsx
./data/db/evalvault_run_026a47a9-c373-4cbb-8f1d-bee004df2928.xlsx
./data/db/evalvault_run_03ab7fd0-fc70-4d82-86dd-05096f914d7a.xlsx
./data/db/evalvault_run_04da6d5c-def9-4b98-b9b9-04dafcda5300.xlsx
./data/db/evalvault_run_0528d7a0-3324-4c91-b02f-88e9a1d01c8b.xlsx
./data/db/evalvault_run_05aacc61-9502-4ebc-b211-8bfd10d1d041.xlsx
./data/db/evalvault_run_077aa840-cf9c-4d9c-a30c-2267fed627d3.xlsx
./data/db/evalvault_run_090eb89a-8b1d-475e-a1f2-a4b247d3cae7.xlsx
./data/db/evalvault_run_0bc819c3-6509-43be-9134-9256b7f141ca.xlsx
./data/db/evalvault_run_0c0515df-9c45-4100-8e09-3bc2f7aae0fc.xlsx
./data/db/evalvault_run_0c4e97b2-4379-49f1-9ba1-56cd2d7ac562.xlsx
./data/db/evalvault_run_0d874126-3ac3-48e1-a108-e351c54ebcca.xlsx
./data/db/evalvault_run_0dc932d9-8f3a-42f0-8717-40a92998f3bf.xlsx
./data/db/evalvault_run_101ada34-920a-494b-9956-8b853145ec1b.xlsx
./data/db/evalvault_run_108db8b1-a826-4dea-948c-30428b0095da.xlsx
./data/db/evalvault_run_10ce749c-a3dd-4997-aaf6-19920c2572e7.xlsx
./data/db/evalvault_run_1115c9b2-0c59-40b7-8c27-9b6e766b72eb.xlsx
./data/db/evalvault_run_127860f3-3ca6-41f6-86f7-b193d9e201a1.xlsx
./data/db/evalvault_run_12a9d971-5af0-45a7-9c37-de244a730676.xlsx
./data/db/evalvault_run_12d9a740-4003-43fd-a440-12d7d6a63a6c.xlsx
./data/db/evalvault_run_140e7731-8f12-41ce-ae79-9db0295b468f.xlsx
./data/db/evalvault_run_145cb83f-58ab-469f-8fe6-c06a07c865aa.xlsx
./data/db/evalvault_run_1507a374-91e1-4764-a8d1-0d5642dc091f.xlsx
./data/db/evalvault_run_16072517-6277-4b1b-a192-c3b4f0af8147.xlsx
./data/db/evalvault_run_17471c5f-ce27-4d29-a2b2-56cc5d79ef88.xlsx
./data/db/evalvault_run_17e8542c-8684-440a-be31-8e411ed3cc0a.xlsx
./data/db/evalvault_run_1946e831-2eef-434e-919d-3e3fb0d91967.xlsx
./data/db/evalvault_run_197ecbfe-6810-4fe1-a579-ee1f66bce2d1.xlsx
./data/db/evalvault_run_1a0e1493-2769-4755-91e4-6bd140d4fc4c.xlsx
./data/db/evalvault_run_1aa2548a-3411-4ba6-a177-3789fa3ea9cf.xlsx
./data/db/evalvault_run_1cab28c9-d30f-4394-af1c-2441b05811e8.xlsx
./data/db/evalvault_run_1cacac34-a49b-4bf1-9ebe-325fa4d4fb40.xlsx
./data/db/evalvault_run_1d150bb2-e5c8-40e6-a282-6d0799fc5427.xlsx
./data/db/evalvault_run_1e940662-8be4-4aae-987d-bba7e22ff526.xlsx
./data/db/evalvault_run_1fb14e94-cffc-41fd-9ee0-b1618fdad4cf.xlsx
./data/db/evalvault_run_1fca88f2-0230-4102-8b0a-23753df6fb0e.xlsx
./data/db/evalvault_run_20461915-04b9-49a8-a702-2757bfeeceb5.xlsx
./data/db/evalvault_run_20d63902-ed3b-4660-8f69-97419617ff59.xlsx
./data/db/evalvault_run_215d4792-cba4-4cb4-b4f6-5db9c85ec392.xlsx
./data/db/evalvault_run_233aa11e-4c66-4fc8-971f-a5583f523d7e.xlsx
./data/db/evalvault_run_23594bfc-a3f5-4d1d-b269-d95478d2507e.xlsx
./data/db/evalvault_run_2588858c-4d61-4d93-af18-9bdbeab73872.xlsx
./data/db/evalvault_run_29534005-135e-4fd2-87e2-10775fa18c9c.xlsx
./data/db/evalvault_run_2a26a2ce-bdb8-44d0-8612-0130d78552d2.xlsx
./data/db/evalvault_run_2b56bfbb-0117-48ce-b39d-188280d94ead.xlsx
./data/db/evalvault_run_2bc07198-614d-4931-9bee-a6cf912267f8.xlsx
./data/db/evalvault_run_2c334602-0a5d-4123-9656-bd3a7cee932b.xlsx
./data/db/evalvault_run_2c67bc66-56c3-4b72-a463-ce880f52fdf4.xlsx
./data/db/evalvault_run_2ce54d3c-95cc-44f9-9289-727fa287d4e2.xlsx
./data/db/evalvault_run_2d5a89fb-deae-4dae-8748-a0104f0a9ce3.xlsx
./data/db/evalvault_run_2db07d07-faad-4d7e-9c16-f8d173b6aded.xlsx
./data/db/evalvault_run_2de05b2c-6ce5-4803-86db-6979d74c9c1e.xlsx
./data/db/evalvault_run_2e495f28-020f-4a64-a644-b136c1e8839e.xlsx
./data/db/evalvault_run_2e8b9463-7304-41be-88a2-ac92aa3abfbb.xlsx
./data/db/evalvault_run_2ec038a5-efed-4cee-985f-26c67d6773b6.xlsx
./data/db/evalvault_run_2fbbd4de-bdff-45f0-a15a-88ae151d5256.xlsx
./data/db/evalvault_run_2fd24aa8-a827-46bc-83b3-fd4e121f9e1d.xlsx
./data/db/evalvault_run_3072ca61-42f1-489f-881e-becc1ced6504.xlsx
./data/db/evalvault_run_31375ae8-09f6-4827-a5a8-68646b168874.xlsx
./data/db/evalvault_run_3156966d-39cb-424d-bec6-b7d4a055448e.xlsx
./data/db/evalvault_run_32be84d5-88bd-4844-b5b5-3776232dd9c9.xlsx
./data/db/evalvault_run_33505410-7148-4101-bb15-e35784d1705f.xlsx
./data/db/evalvault_run_34aba331-407f-49ca-9912-8d403cc8db9c.xlsx
./data/db/evalvault_run_3584d1be-2577-46ef-b861-59db7ead5d5a.xlsx
./data/db/evalvault_run_3595d7ea-66c5-4064-a912-4ab5e0c4bf5d.xlsx
./data/db/evalvault_run_368eb1d3-1a15-4117-9740-f6885827c803.xlsx
./data/db/evalvault_run_36b5011d-ad72-4cfa-aaa3-bc69004ef244.xlsx
./data/db/evalvault_run_3787d433-e141-42ee-9860-469dee0aadef.xlsx
./data/db/evalvault_run_37942d43-2843-4d5c-ab61-fbd31cfe16ea.xlsx
./data/db/evalvault_run_37c6f7d5-7811-45b9-b9fe-980cc0c18f13.xlsx
./data/db/evalvault_run_37d298a7-cebc-4d0e-99b5-d3ca88544aae.xlsx
./data/db/evalvault_run_388ac7c6-2d24-4fcc-8ef3-86f8f24eb6ea.xlsx
./data/db/evalvault_run_38aae8ba-6e3b-496f-8a23-f3d7dfef93f2.xlsx
./data/db/evalvault_run_38d67d7f-befb-4d6f-b075-16606234e7f8.xlsx
./data/db/evalvault_run_3b0820ad-d16f-4ef3-994b-4253f490a626.xlsx
./data/db/evalvault_run_3b578f84-5c45-4f13-a993-71de27028991.xlsx
./data/db/evalvault_run_3ca7d049-67d0-4da4-b3bc-7a17ea4c537c.xlsx
./data/db/evalvault_run_3cf354a9-8132-4a78-81ee-e1cab277b52c.xlsx
./data/db/evalvault_run_3d30147a-bef2-4eb7-a2ab-790a1330325d.xlsx
./data/db/evalvault_run_3d47835e-ed78-4103-b2f9-b811e455bcd1.xlsx
./data/db/evalvault_run_3d8c1565-7a1c-4ada-b00a-2656089f72f3.xlsx
./data/db/evalvault_run_3e0e8ff1-aa20-4578-9654-90a7be934c25.xlsx
./data/db/evalvault_run_3eead056-9c9c-4a97-8525-7f5ab152707a.xlsx
./data/db/evalvault_run_3fd6e25f-e906-421d-a37d-fde31d876aac.xlsx
./data/db/evalvault_run_41efcecd-c478-404b-9e2d-2346b39128b4.xlsx
./data/db/evalvault_run_41fac1d1-18dc-4051-8ca0-ea584a6ad24f.xlsx
./data/db/evalvault_run_4250bf07-5e06-493f-a26a-ca8a26ace9c9.xlsx
./data/db/evalvault_run_433717ad-3279-40d8-9ff9-122371198bd6.xlsx
./data/db/evalvault_run_4365d376-126f-456d-b11c-6faefcdc1b89.xlsx
./data/db/evalvault_run_47125eec-9ed5-4d5f-921c-1af8acf45d09.xlsx
./data/db/evalvault_run_476e1abd-45c7-404a-b698-a18578bf5f65.xlsx
./data/db/evalvault_run_48b72052-dba9-4771-a442-b192a2da2927.xlsx
./data/db/evalvault_run_48c94f63-6ad8-4a65-9652-7a7d06472c86.xlsx
./data/db/evalvault_run_49961f02-6659-41ea-9b6e-30db3fddca7b.xlsx
./data/db/evalvault_run_49cdc6a1-6945-409a-98f0-9e2fa35d8d54.xlsx
./data/db/evalvault_run_49dec022-9240-49f8-abb8-0de5cdd932c2.xlsx
./data/db/evalvault_run_4a268eef-4b1b-4102-b407-1cf6fd00bf53.xlsx
./data/db/evalvault_run_4a8e8a52-b2a7-40af-8639-620fb64f74a7.xlsx
./data/db/evalvault_run_4a9795b0-1bea-45a3-80cb-3a0209d5b186.xlsx
./data/db/evalvault_run_4b2cbcad-2162-4745-840c-68411b5d7cd4.xlsx
./data/db/evalvault_run_4b6f8fc8-046e-457a-9004-176fd1b25ec5.xlsx
./data/db/evalvault_run_4c897121-acca-478c-a084-1aece48d5aba.xlsx
./data/db/evalvault_run_4d194db0-085f-491d-bf53-4f54a20fe128.xlsx
./data/db/evalvault_run_4d2a17a0-5990-4133-a1d0-9a8f14028fd9.xlsx
./data/db/evalvault_run_4dc8af27-bae8-4a5c-9b1e-c57b1402a2f4.xlsx
./data/db/evalvault_run_4e336103-5983-4e09-a0aa-74926ef36905.xlsx
./data/db/evalvault_run_4f0a6373-091e-45d4-9e65-c96b539b1350.xlsx
./data/db/evalvault_run_4f2d9b36-a76e-4208-873b-b5c6b14e2795.xlsx
./data/db/evalvault_run_4f4a3985-07c5-4bcc-892e-08c652424604.xlsx
./data/db/evalvault_run_502851c0-cc95-48ac-befb-ff7178f6a8b5.xlsx
./data/db/evalvault_run_521b1eaf-8f38-4f32-943e-782193ba6f31.xlsx
./data/db/evalvault_run_5297ad43-c3c0-48d0-99ef-5795bc723a70.xlsx
./data/db/evalvault_run_52d13133-4e4a-47de-85e0-b82a2c051171.xlsx
./data/db/evalvault_run_536351b5-b622-45d9-8338-eb45f95db876.xlsx
./data/db/evalvault_run_53ab1f6b-5f09-4837-b361-5860539c5a64.xlsx
./data/db/evalvault_run_546a8b8f-16e6-43d9-924d-8e653d6d62d2.xlsx
./data/db/evalvault_run_5601ed41-435b-4214-8e9d-97bb4797642c.xlsx
./data/db/evalvault_run_562e7ecf-74c9-4b33-8ce5-dca73f8e0bea.xlsx
./data/db/evalvault_run_57c09f5d-bfb9-4014-9e04-ba7acee550c4.xlsx
./data/db/evalvault_run_59b6c49a-234f-4271-910e-40dcccb3b6b1.xlsx
./data/db/evalvault_run_5a32bde9-292b-4a77-82f9-a2abc02f1110.xlsx
./data/db/evalvault_run_5b6917f8-6601-4034-8adc-03ea1312a505.xlsx
./data/db/evalvault_run_5be2356e-44b1-4f16-8680-0de9ff30d0e0.xlsx
./data/db/evalvault_run_5c0050b2-424a-47f5-9430-9cb60c6c1ff8.xlsx
./data/db/evalvault_run_5c161ec3-e8df-4939-8458-27594dea27e9.xlsx
./data/db/evalvault_run_5c24d14e-ae4e-460b-a6bd-ed4e6f16b64e.xlsx
./data/db/evalvault_run_5c5522e7-55fa-4c91-8a2a-257449afcf26.xlsx
./data/db/evalvault_run_5d40602b-6570-4ba2-9b1d-85f4a06f68ae.xlsx
./data/db/evalvault_run_5da68fb5-c012-46e4-a4f8-92d88f06fdab.xlsx
./data/db/evalvault_run_5e55330f-5888-4645-8d5b-35db58c0fb6a.xlsx
./data/db/evalvault_run_5e9f41bd-94c4-4cbd-aec0-3c713ebd7c96.xlsx
./data/db/evalvault_run_5f74185a-d738-4ba5-90ff-7cd9ec26ee55.xlsx
./data/db/evalvault_run_60e3865f-8c89-4634-a061-90085de90802.xlsx
./data/db/evalvault_run_60e68d09-6b69-45ae-8005-c1e5431a39e9.xlsx
./data/db/evalvault_run_60f04945-14f2-4905-8cc0-247db30669b0.xlsx
./data/db/evalvault_run_624bbcdf-9013-40b9-afd8-263f70199509.xlsx
./data/db/evalvault_run_626d56df-d716-4dee-9065-b5938ab44623.xlsx
./data/db/evalvault_run_62e2b274-448f-456c-88c7-cc68b2ab025c.xlsx
./data/db/evalvault_run_64486cbc-921b-4ca1-9f79-5819e8a04c7c.xlsx
./data/db/evalvault_run_648f2371-6efe-4667-8af6-89dd6d8fcb03.xlsx
./data/db/evalvault_run_64c9f997-1ba9-485c-a213-dfd1b41067c3.xlsx
./data/db/evalvault_run_651bcd16-464f-42d3-a539-f4d18de9f5c5.xlsx
./data/db/evalvault_run_6526ff1c-2ada-4ff1-8146-d34bec69a711.xlsx
./data/db/evalvault_run_660592a6-6717-4ef7-8bb9-f4a1f4d7d1d6.xlsx
./data/db/evalvault_run_660a9c2b-d037-4986-b1e1-0b0a443e0ee9.xlsx
./data/db/evalvault_run_664812d8-d918-4c44-b473-b330aa56a5b4.xlsx
./data/db/evalvault_run_667b4443-77da-4c28-9676-701e14048edf.xlsx
./data/db/evalvault_run_66992edf-b380-4411-84fa-ad71f95425f9.xlsx
./data/db/evalvault_run_66b8793d-5106-4831-a63b-6fe814a1178a.xlsx
./data/db/evalvault_run_67422936-c498-44f3-a812-2d0fbd08d6bb.xlsx
./data/db/evalvault_run_67dea70b-32bf-457c-98b9-3190151eb6b6.xlsx
./data/db/evalvault_run_67e154c3-8481-4126-a900-d4564c3207c7.xlsx
./data/db/evalvault_run_6813b46a-3322-4867-91bd-2018b1ea5e9b.xlsx
./data/db/evalvault_run_68c1dfe5-9dfb-47bf-852c-1252ed2381f5.xlsx
./data/db/evalvault_run_69efa4c9-dbc6-4e6a-91da-14ac1b4ca0aa.xlsx
./data/db/evalvault_run_6b5ac263-90fc-4ee1-a0c9-ead6aedc1bc1.xlsx
./data/db/evalvault_run_6d825c11-7786-4db1-8e69-fa1641526383.xlsx
./data/db/evalvault_run_6d9dedd0-b38c-439e-a1d0-c29d4e2e4a8e.xlsx
./data/db/evalvault_run_6df68d64-0d8e-4ca0-8195-f4631df3c4b1.xlsx
./data/db/evalvault_run_6f54e407-1e47-4909-9044-698d26bdccf0.xlsx
./data/db/evalvault_run_7002a2ae-32f5-4e23-a84b-cd8918008497.xlsx
./data/db/evalvault_run_7023b35b-ff13-4cfc-b93d-a6491137bdab.xlsx
./data/db/evalvault_run_70e81f18-a73b-498d-b365-af947c903107.xlsx
./data/db/evalvault_run_7119085a-2e71-4ad6-8700-80182906b6e7.xlsx
./data/db/evalvault_run_72b30abe-9bfa-400b-a657-a1656c4e0902.xlsx
./data/db/evalvault_run_730f89b6-7623-4405-9939-83acf94bf2d2.xlsx
./data/db/evalvault_run_73e8b2f5-f54d-408b-b8db-465cd5d95d92.xlsx
./data/db/evalvault_run_73f974a2-91fd-4560-9881-b33d706fd269.xlsx
./data/db/evalvault_run_745f7188-a243-4d56-98b8-09b278cea6b7.xlsx
./data/db/evalvault_run_746ef4f6-4e89-4dca-a040-e5d7b6e40299.xlsx
./data/db/evalvault_run_747dfb20-6e5f-4f07-956a-06e611f4454d.xlsx
./data/db/evalvault_run_74820c60-319f-482f-90fc-30d13b3e8b2d.xlsx
./data/db/evalvault_run_758ab90e-f8ea-4410-9923-d75d7448a4c2.xlsx
./data/db/evalvault_run_76bf9307-b4d5-4a49-98fd-6532bbec4d2f.xlsx
./data/db/evalvault_run_779ae0ab-0e56-4f9b-87e1-c0b6349e81fa.xlsx
./data/db/evalvault_run_77af727c-3f66-4536-a871-2683fd1ee0a0.xlsx
./data/db/evalvault_run_7879bb40-6c11-403b-894b-b0c397081f0f.xlsx
./data/db/evalvault_run_78e6cd0e-43fb-46dd-b182-e12887bf8bb4.xlsx
./data/db/evalvault_run_7ae91110-a7b0-49fb-ad0f-f0718ed2b1e4.xlsx
./data/db/evalvault_run_7b300962-1530-4323-9af2-7fc2bc38f29c.xlsx
./data/db/evalvault_run_7b698ba6-beaf-41d4-85cd-6ae57c54818d.xlsx
./data/db/evalvault_run_7bb5eaa9-dc17-412a-a42b-ba92279b5311.xlsx
./data/db/evalvault_run_7bef1ea7-442e-455f-9c88-e731e37899f5.xlsx
./data/db/evalvault_run_7e72bea6-e786-4e45-b3a7-e6e7ae2a2997.xlsx
./data/db/evalvault_run_7e896e32-28a6-4ac5-93f7-261c1abf9e2c.xlsx
./data/db/evalvault_run_7e9106fc-d2db-4a52-8e31-83214198b3aa.xlsx
./data/db/evalvault_run_7ecb24d8-176e-4efc-9dde-dc6b2865df6a.xlsx
./data/db/evalvault_run_810cc0c8-f467-4ce7-bcaa-660f9cf7efb8.xlsx
./data/db/evalvault_run_83082904-b671-423c-8fda-40ae0014db5f.xlsx
./data/db/evalvault_run_83d38473-2608-4198-a5e7-373c0452d73d.xlsx
./data/db/evalvault_run_83fc84bb-fd66-4db9-975c-a1bfdcecf9d5.xlsx
./data/db/evalvault_run_84ac5d1f-cce7-4540-bf9a-06d5ee42228c.xlsx
./data/db/evalvault_run_84f1de99-01f8-45c9-9f8f-1c4c32b4c44c.xlsx
./data/db/evalvault_run_850c786e-50ec-4b41-b3f6-c726380d8680.xlsx
./data/db/evalvault_run_853664f6-518c-4306-92a1-fc13542d7254.xlsx
./data/db/evalvault_run_854ff79f-2106-4ab0-9b90-32bac55a52e2.xlsx
./data/db/evalvault_run_861e3277-10fe-4f9d-b41c-51f7982bdb73.xlsx
./data/db/evalvault_run_86c2bd5b-88f0-462b-96a8-03ce835cbdf2.xlsx
./data/db/evalvault_run_86e93743-3423-4568-87f4-ca092b4852be.xlsx
./data/db/evalvault_run_871a0361-0168-469e-94bf-046cb04249a0.xlsx
./data/db/evalvault_run_8854fbbd-bd0f-4022-9929-0bac014aa289.xlsx
./data/db/evalvault_run_8a961371-d402-4880-b5e2-9a35bff5a5d4.xlsx
./data/db/evalvault_run_8b015c2e-d8dd-4057-adcc-6197a9da110e.xlsx
./data/db/evalvault_run_8b081bf0-dd04-4170-a09d-04d72d5e420d.xlsx
./data/db/evalvault_run_8b6cf7a1-dfba-4c9c-903b-4aeb0d2d6474.xlsx
./data/db/evalvault_run_8c3bedfd-45f6-4081-b7ba-2ef5c68b0035.xlsx
./data/db/evalvault_run_8c668d4d-2c0d-4d3f-a3c0-79512e56ceb5.xlsx
./data/db/evalvault_run_8cfbb0a4-a79d-4719-a50a-5cb09e0d33f7.xlsx
./data/db/evalvault_run_904ad834-ceff-4909-971c-ae7ccc2238e7.xlsx
./data/db/evalvault_run_942e79c4-58fb-4ce3-9ea6-3f08257c6dc7.xlsx
./data/db/evalvault_run_94491b3e-4c0d-424f-8121-2d76f4324089.xlsx
./data/db/evalvault_run_94a0c74f-6472-4c8c-bfa0-05785565903d.xlsx
./data/db/evalvault_run_95973db8-478d-4529-ad28-5dd5a77f9bf1.xlsx
./data/db/evalvault_run_95add858-0f41-4d1c-a236-b30465ffdb58.xlsx
./data/db/evalvault_run_95d6481c-11d1-44ba-9b93-406b3033c535.xlsx
./data/db/evalvault_run_967c437b-0028-4cec-85ed-7ded9216713d.xlsx
./data/db/evalvault_run_9699dacc-a968-4fe3-a141-fd0efc4ae2ab.xlsx
./data/db/evalvault_run_96b6cf33-f127-44da-bf14-a25442602142.xlsx
./data/db/evalvault_run_97a44e0c-8ea7-48ca-a78c-87a762b6e7de.xlsx
./data/db/evalvault_run_99a42b54-ffe1-4b76-b563-6a02fecee5a9.xlsx
./data/db/evalvault_run_99fce94b-bec1-4f93-a57d-e2500220571d.xlsx
./data/db/evalvault_run_9a08cad0-4187-4b73-b73e-a709daf379b7.xlsx
./data/db/evalvault_run_9a137e92-e773-4016-bc36-a12313087cdb.xlsx
./data/db/evalvault_run_9aa11159-c147-4c62-8314-63ef58a82ce4.xlsx
./data/db/evalvault_run_9d87889c-ee86-40ae-b945-98c16da158c5.xlsx
./data/db/evalvault_run_9dc707fa-8b1c-4c56-b105-6e7bb7bd4f7e.xlsx
./data/db/evalvault_run_9e7ecf86-78ff-4c3c-9f78-471eecc762b8.xlsx
./data/db/evalvault_run_a05f055a-1327-464c-a04e-2317211629b4.xlsx
./data/db/evalvault_run_a0b122ad-dc85-4209-a8c1-b34e14d476d5.xlsx
./data/db/evalvault_run_a0c4fed1-9468-4383-bf8f-2bb679e49430.xlsx
./data/db/evalvault_run_a20f9c82-76bb-4f20-9eac-0dbde35f8d10.xlsx
./data/db/evalvault_run_a2289511-6689-406f-9a8e-b159d04e72b7.xlsx
./data/db/evalvault_run_a40f6f4f-b237-4bfe-92d7-10119473e920.xlsx
./data/db/evalvault_run_a5b43855-b5b1-443c-a9f8-4490447370ea.xlsx
./data/db/evalvault_run_a6abc2a8-a6ce-46f8-ae81-231ebf1d179a.xlsx
./data/db/evalvault_run_a6f72d11-bd87-4759-ac04-6e7e8147408e.xlsx
./data/db/evalvault_run_a6f86cba-85a9-487d-b654-5e9e9e30c8db.xlsx
./data/db/evalvault_run_a75281a8-0f36-4337-b526-ace22273466a.xlsx
./data/db/evalvault_run_a77d8761-13cb-497c-8cc7-7ce17cbb70b5.xlsx
./data/db/evalvault_run_a95048fc-428e-4263-92c7-9c7417827212.xlsx
./data/db/evalvault_run_a9fd1bc1-f095-4917-96be-bf8e28ed7d76.xlsx
./data/db/evalvault_run_aa4828b5-f36f-4f12-acac-15c551f3b70a.xlsx
./data/db/evalvault_run_aabb43e8-6594-4389-83d9-7c7ce77355c3.xlsx
./data/db/evalvault_run_aadbc07a-0d5a-4175-b273-76303e679512.xlsx
./data/db/evalvault_run_aae53482-87ff-4330-b9f5-d1a264e929af.xlsx
./data/db/evalvault_run_ab379baa-0cee-447c-baee-98acf765bc5b.xlsx
./data/db/evalvault_run_abb9ec61-4d4d-4afd-8473-c3f0b18c1d9f.xlsx
./data/db/evalvault_run_ac0c8f32-8b39-41a4-8992-38e0f35e5c37.xlsx
./data/db/evalvault_run_ad31d518-6e2c-4cfb-8307-62a08e23c5b1.xlsx
./data/db/evalvault_run_ade8a795-ebd1-410d-9751-f75711d71339.xlsx
./data/db/evalvault_run_b01ec923-3249-40a4-b8ad-71c432b10cc7.xlsx
./data/db/evalvault_run_b069b54c-7bc4-4f44-a5c8-150cc7f4cccb.xlsx
./data/db/evalvault_run_b44d33c6-4e63-463f-af1c-f36ebed9ac1c.xlsx
./data/db/evalvault_run_b5227c3f-4b73-44a0-98a9-b470e0c8c7ae.xlsx
./data/db/evalvault_run_b577afcc-2bfe-429f-9b74-03a338444702.xlsx
./data/db/evalvault_run_b5b4d80f-2062-464b-b4fd-8aed94cf1ab0.xlsx
./data/db/evalvault_run_b6058a48-66b9-484e-a100-12d821ea7d99.xlsx
./data/db/evalvault_run_b64f5698-9449-4405-9314-8138a72e75fc.xlsx
./data/db/evalvault_run_b766a211-d778-47a6-84ae-68dbddbf6246.xlsx
./data/db/evalvault_run_ba7a5414-da9c-4889-8838-9dd839b94b78.xlsx
./data/db/evalvault_run_ba8b9fae-dfc6-4800-a762-c03bcb78508f.xlsx
./data/db/evalvault_run_bab778e9-2b6d-47bb-b0de-b5b4cce67466.xlsx
./data/db/evalvault_run_bb4d8f3d-30c0-4b67-8869-760c5c57b744.xlsx
./data/db/evalvault_run_bcadc2fb-6b4f-4ec3-9bab-53a664b3efaa.xlsx
./data/db/evalvault_run_c058ed76-dd7a-4942-8aeb-d74f3952c057.xlsx
./data/db/evalvault_run_c14f98a4-f449-4350-8f7a-0468f2564dfd.xlsx
./data/db/evalvault_run_c186197d-75ac-4627-9447-884ed033a5ec.xlsx
./data/db/evalvault_run_c19b44eb-784c-4104-8eba-3662668b0095.xlsx
./data/db/evalvault_run_c1dd89bc-9f5d-401f-b281-d8fcb1cdf981.xlsx
./data/db/evalvault_run_c28ebffb-497f-4c1f-b663-fee1299dab9f.xlsx
./data/db/evalvault_run_c3307ab7-899d-40e4-910b-3d72812a52fd.xlsx
./data/db/evalvault_run_c3b3042c-0ab5-4291-906a-0a94a74db0b2.xlsx
./data/db/evalvault_run_c3f77310-49b3-4001-8ea6-f1c89dafceaa.xlsx
./data/db/evalvault_run_c42e95b5-735c-4439-87d9-c86df4720443.xlsx
./data/db/evalvault_run_c4ada3ab-d335-42f1-ac38-bc4f1e0e6273.xlsx
./data/db/evalvault_run_c4bbc9e9-054f-4840-a21d-fcd978a8fb16.xlsx
./data/db/evalvault_run_c4fceb0c-c5e4-49ab-814e-8f7de2d2e962.xlsx
./data/db/evalvault_run_c5729e79-a9f6-467f-be42-6057717183ff.xlsx
./data/db/evalvault_run_c595ac87-172f-49aa-97d9-52229b37361e.xlsx
./data/db/evalvault_run_c9625017-701a-4a93-9daf-3e3cbeb7dce1.xlsx
./data/db/evalvault_run_ca6b1796-585a-4166-9546-e34c22386c2c.xlsx
./data/db/evalvault_run_cb25200f-20ff-4232-a8a9-cfc1bede313b.xlsx
./data/db/evalvault_run_cb49db2f-63bc-4d6e-8339-4461d0b9eff1.xlsx
./data/db/evalvault_run_cb66237c-9ae0-4e21-8049-4d27e55c95f9.xlsx
./data/db/evalvault_run_cbb8a2d0-7b89-4bf7-8ccb-b53ddf1e6a5f.xlsx
./data/db/evalvault_run_ccabf600-18c3-4bc3-94fd-552804476277.xlsx
./data/db/evalvault_run_cd2f2379-02ce-4f50-928d-03d127281f8d.xlsx
./data/db/evalvault_run_cd72dc08-a020-4745-b30f-d7dc8085c7d2.xlsx
./data/db/evalvault_run_cde5c048-0423-4d6e-b86b-4e9752515333.xlsx
./data/db/evalvault_run_d05a984a-9a3a-4f5e-ba14-53df740e8ff2.xlsx
./data/db/evalvault_run_d0b2dc79-cbb7-4240-b167-f8f048d33988.xlsx
./data/db/evalvault_run_d1101a80-a6c5-429e-9ba0-4c9016df9157.xlsx
./data/db/evalvault_run_d1745d63-5e65-4f24-9ddc-45d342a63332.xlsx
./data/db/evalvault_run_d17be6d0-a2d9-471a-84ba-11b8f710730c.xlsx
./data/db/evalvault_run_d1ac41b0-609d-4f7a-b760-10ab6111def9.xlsx
./data/db/evalvault_run_d37b328b-605e-4efd-98f4-4e91e9e749c7.xlsx
./data/db/evalvault_run_d603bc7e-fbe0-4a13-a257-66a791f4bf21.xlsx
./data/db/evalvault_run_d6472edd-9e07-4b73-9baf-addc0fb2717d.xlsx
./data/db/evalvault_run_d648258a-443e-47b1-b8bb-1c90807ea531.xlsx
./data/db/evalvault_run_d682114e-45f2-4427-8dff-2739574ce733.xlsx
./data/db/evalvault_run_d6f5ef41-70dd-4e77-9b95-6738d5c964bd.xlsx
./data/db/evalvault_run_d701e72c-4eb4-4656-8809-999b468883e2.xlsx
./data/db/evalvault_run_d7c25cf2-dc61-4974-aaff-ccd14e3823a6.xlsx
./data/db/evalvault_run_d7e30a5f-d093-4802-ab6e-414454c6db0a.xlsx
./data/db/evalvault_run_d9113f70-ee04-4b6c-939e-a0dcbf64a890.xlsx
./data/db/evalvault_run_d988eadd-ed89-441c-bacd-a5dfbbbaddc2.xlsx
./data/db/evalvault_run_db9fb87e-46e4-4024-b37b-1a33816023df.xlsx
./data/db/evalvault_run_dc5de642-6b34-4163-a114-4cb483323ddc.xlsx
./data/db/evalvault_run_dd6fac8b-e9ca-439c-9127-06a9e8e07824.xlsx
./data/db/evalvault_run_de5a64e4-9985-4780-9105-2a0fc30cee4b.xlsx
./data/db/evalvault_run_dfa68917-b6da-41f1-bf05-d54104348f09.xlsx
./data/db/evalvault_run_e1e634c7-47ea-419b-9a2f-b41509b5864e.xlsx
./data/db/evalvault_run_e28c3a3b-be85-4302-b65f-4615a98725c5.xlsx
./data/db/evalvault_run_e4155a28-4cab-4dfe-a2bd-2e0df2d67560.xlsx
./data/db/evalvault_run_e44ce70e-6621-43f9-8463-2b3979188a76.xlsx
./data/db/evalvault_run_e54cf74b-3091-4cf3-a69c-d667e4fc38a4.xlsx
./data/db/evalvault_run_e5c97788-33b0-4c1d-9a81-cf156598437c.xlsx
./data/db/evalvault_run_e60eebd7-b2c4-40d1-8980-b8bb59170875.xlsx
./data/db/evalvault_run_e7bceaca-6aee-4df5-879f-47d774790e3d.xlsx
./data/db/evalvault_run_e7e37328-8a80-4572-8a5a-43d46b9a885b.xlsx
./data/db/evalvault_run_e84c44b9-1e8b-4f2e-a8db-c6ae6b598ddb.xlsx
./data/db/evalvault_run_e870a6a7-682a-48ac-b09e-b2660dec21c7.xlsx
./data/db/evalvault_run_e8fe34ca-2928-4fe6-a14a-8383fb4f0e53.xlsx
./data/db/evalvault_run_e91fc5d5-4e64-4fbf-84d2-31a3e82b425f.xlsx
./data/db/evalvault_run_ead3872f-666d-48ab-9e27-78a0be842490.xlsx
./data/db/evalvault_run_eaeefde9-78a4-4f46-b746-2e98617f9338.xlsx
./data/db/evalvault_run_eb30c763-a03f-4153-bb21-b945ce055899.xlsx
./data/db/evalvault_run_ecf16af6-0191-4e31-8806-a2b63bc097b2.xlsx
./data/db/evalvault_run_ed709b2e-150f-4c56-8f21-86c0831d0252.xlsx
./data/db/evalvault_run_ed994516-07cb-4a52-a0d7-42648fe804ee.xlsx
./data/db/evalvault_run_ee009863-a987-4958-b62c-1c492427eb68.xlsx
./data/db/evalvault_run_ef05b249-2d1c-4bc3-91e7-ccf2e78aef3e.xlsx
./data/db/evalvault_run_efed980d-6b33-4bab-859a-bda1a637a08e.xlsx
./data/db/evalvault_run_f05b4376-0117-4373-8ac9-5105c846f53b.xlsx
./data/db/evalvault_run_f411f3cc-cf92-4886-9d80-f572670bd2a2.xlsx
./data/db/evalvault_run_f4aee7b9-bfee-41c8-871b-9ddc29e72551.xlsx
./data/db/evalvault_run_f50b8779-1b67-42bd-a8f2-92efbc3bf61b.xlsx
./data/db/evalvault_run_f58ca51a-9429-4eed-8b2f-6cb4ec1f7f5b.xlsx
./data/db/evalvault_run_f58e999c-53f9-464a-a670-7cec0fa101a2.xlsx
./data/db/evalvault_run_f673ef01-4ce6-4ae9-996e-26bb9aa93a63.xlsx
./data/db/evalvault_run_f744a821-f57e-4ce3-8d9b-c3d4e1fec35c.xlsx
./data/db/evalvault_run_f7a6c976-ef1c-4e38-affe-78a4755382d2.xlsx
./data/db/evalvault_run_f84f2539-753d-40ad-80ac-d5ce51f4dd2e.xlsx
./data/db/evalvault_run_f8c3d298-32f7-4d80-8947-259c49c69390.xlsx
./data/db/evalvault_run_f8d3b612-4045-4794-ba87-30aaf3653432.xlsx
./data/db/evalvault_run_f900c4c6-b4e7-4d02-aaff-ec9db737796d.xlsx
./data/db/evalvault_run_f968f32f-ff8f-43f4-84ee-132a05de3ade.xlsx
./data/db/evalvault_run_f9cca87d-ad43-41f2-b562-4718ad402d5a.xlsx
./data/db/evalvault_run_fa5f01e9-5b2f-428b-8ddc-c7dfff2f8492.xlsx
./data/db/evalvault_run_fa6068c9-26b2-4489-81ea-31b49b72007b.xlsx
./data/db/evalvault_run_fa8bf4b9-181c-4147-ad19-d738df77c585.xlsx
./data/db/evalvault_run_fb1f6ca2-9e23-4f5f-911d-0e76bd97d831.xlsx
./data/db/evalvault_run_fb68e29f-261d-4dee-9e11-85fe44c9a3a8.xlsx
./data/db/evalvault_run_fbf23fe1-7c33-4113-9404-12732fe3ccd3.xlsx
./data/db/evalvault_run_fcf25836-d83d-4e54-b7b2-fabae359dc84.xlsx
./data/db/evalvault_run_fd267590-cbb6-4841-8811-fca669a1eaca.xlsx
./data/db/evalvault_run_fe576c72-6a58-4bbf-b6e6-58a229978eab.xlsx
./data/db/evalvault_run_fec0c8cd-00a0-49c8-bb96-695b712455c5.xlsx
./data/db/evalvault_run_fec3631a-c091-4326-9e1b-52cfe4bf4386.xlsx
./data/db/evalvault_run_feebe396-1d73-44e2-8f0d-08fb3a080d30.xlsx
./data/db/evalvault_run_ff39e1de-e15b-419d-a471-04be10dd8bab.xlsx
./data/e2e_results/e2e_evaluations.db
./data/e2e_results/summary_eval_minimal_custom.json
./data/e2e_results/summary_eval_minimal_custom.xlsx
./data/e2e_results/summary_eval_minimal_probe.json
./data/e2e_results/summary_eval_single_case.json
./data/e2e_results/summary_eval_single_case.xlsx
./data/e2e_results/summary_eval_single_case_prompt.json
./data/evaluations.db
./data/evalvault.db
./data/kg/knowledge_graph.json
./data/rag/user_guide_bm25.json
./data/raw/The Complete Guide to Mastering Suno Advanced Strategies for Professional Music Generation.md
./data/raw/doc.txt
./data/raw/edge_cases.json
./data/raw/run_mode_full_domain_memory.json
./data/raw/sample_rag_knowledge.txt
./dataset_templates/dataset_template.csv
./dataset_templates/dataset_template.json
./dataset_templates/dataset_template.xlsx
./dataset_templates/method_input_template.json
./docker-compose.langfuse.yml
./docker-compose.offline.yml
./docker-compose.phoenix.yaml
./docker-compose.yml
./docs/INDEX.md
./docs/README.ko.md
./docs/ROADMAP.md
./docs/STATUS.md
./docs/api/adapters/inbound.md
./docs/api/adapters/outbound.md
./docs/api/config.md
./docs/api/domain/entities.md
./docs/api/domain/metrics.md
./docs/api/domain/services.md
./docs/api/ports/inbound.md
./docs/api/ports/outbound.md
./docs/architecture/open-rag-trace-collector.md
./docs/architecture/open-rag-trace-spec.md
./docs/getting-started/INSTALLATION.md
./docs/guides/AGENTS_SYSTEM_GUIDE.md
./docs/guides/CHAINLIT_INTEGRATION_PLAN.md
./docs/guides/CI_REGRESSION_GATE.md
./docs/guides/CLI_MCP_PLAN.md
./docs/guides/CLI_PARALLEL_FEATURES_SPEC.md
./docs/guides/CLI_UX_REDESIGN.md
./docs/guides/DEV_GUIDE.md
./docs/guides/DOCS_REFRESH_PLAN.md
./docs/guides/EVALVAULT_DIAGNOSTIC_PLAYBOOK.md
./docs/guides/EVALVAULT_RUN_EXCEL_SHEETS.md
./docs/guides/EVALVAULT_WORK_PLAN.md
./docs/guides/EXTERNAL_TRACE_API_SPEC.md
./docs/guides/Extension_2.md
./docs/guides/Extension_Data_Difficulty_Profiling_Custom_Judge_Model.md
./docs/guides/INSURANCE_SUMMARY_METRICS_PLAN.md
./docs/guides/LENA_MVP_IMPLEMENTATION_PLAN.md
./docs/guides/LENA_RAGAS_CALIBRATION_DEV_PLAN.md
./docs/guides/MULTITURN_EVAL_GUIDE.md
./docs/guides/NEXT_STEPS_EXECUTION_PLAN.md
./docs/guides/OFFLINE_DOCKER.md
./docs/guides/OPEN_RAG_TRACE_INTERNAL_ADAPTER.md
./docs/guides/OPEN_RAG_TRACE_SAMPLES.md
./docs/guides/P0_P3_EXECUTION_REPORT.md
./docs/guides/P1_P4_WORK_PLAN.md
./docs/guides/PARALLEL_WORK_APPROVAL_RULES.md
./docs/guides/PRD_LENA.md
./docs/guides/PROJECT_STATUS_AND_PLAN.md
./docs/guides/RAGAS_HUMAN_FEEDBACK_CALIBRATION_GUIDE.md
./docs/guides/RAG_CLI_WORKFLOW_TEMPLATES.md
./docs/guides/RAG_NOISE_REDUCTION_GUIDE.md
./docs/guides/RAG_PERFORMANCE_IMPLEMENTATION_LOG.md
./docs/guides/RAG_PERFORMANCE_IMPROVEMENT_PROPOSAL.md
./docs/guides/RELEASE_CHECKLIST.md
./docs/guides/USER_GUIDE.md
./docs/guides/WEBUI_CLI_ROLLOUT_PLAN.md
./docs/guides/WORKLOG_LAST_2_DAYS.md
./docs/guides/cli_process.md
./docs/guides/prompt_suggestions_design.md
./docs/guides/rag_human_feedback_calibration_implementation_plan.md
./docs/guides/refactoring_strategy.md
./docs/guides/repeat_query.md
./docs/handbook/appendix-file-inventory.md
./docs/mapping/component-to-whitepaper.yaml
./docs/new_whitepaper/00_frontmatter.md
./docs/new_whitepaper/01_overview.md
./docs/new_whitepaper/02_architecture.md
./docs/new_whitepaper/03_data_flow.md
./docs/new_whitepaper/04_components.md
./docs/new_whitepaper/05_expert_lenses.md
./docs/new_whitepaper/06_implementation.md
./docs/new_whitepaper/07_advanced.md
./docs/new_whitepaper/08_customization.md
./docs/new_whitepaper/09_quality.md
./docs/new_whitepaper/10_performance.md
./docs/new_whitepaper/11_security.md
./docs/new_whitepaper/12_operations.md
./docs/new_whitepaper/13_standards.md
./docs/new_whitepaper/14_roadmap.md
./docs/new_whitepaper/INDEX.md
./docs/new_whitepaper/STYLE_GUIDE.md
./docs/refactor/REFAC_000_master_plan.md
./docs/refactor/REFAC_010_agent_playbook.md
./docs/refactor/REFAC_020_logging_policy.md
./docs/refactor/REFAC_030_phase0_responsibility_map.md
./docs/refactor/REFAC_040_wbs_parallel_plan.md
./docs/refactor/logs/phase-0-baseline.md
./docs/refactor/logs/phase-1-evaluator.md
./docs/refactor/logs/phase-2-cli-run.md
./docs/refactor/logs/phase-3-analysis.md
./docs/security_audit_worklog.md
./docs/stylesheets/extra.css
./docs/templates/dataset_template.csv
./docs/templates/dataset_template.json
./docs/templates/dataset_template.xlsx
./docs/templates/eval_report_templates.md
./docs/templates/kg_template.json
./docs/templates/otel_openinference_trace_example.json
./docs/templates/ragas_dataset_example_ko90_en10.json
./docs/templates/retriever_docs_template.json
./docs/tools/generate-whitepaper.py
./docs/web_ui_analysis_migration_plan.md
./dummy_test_dataset.json
./evalvault.db
./evalvault_memory.db
./examples/README.md
./examples/benchmarks/README.md
./examples/benchmarks/korean_rag/faithfulness_test.json
./examples/benchmarks/korean_rag/insurance_qa_100.json
./examples/benchmarks/korean_rag/keyword_extraction_test.json
./examples/benchmarks/korean_rag/retrieval_test.json
./examples/benchmarks/output/comparison.json
./examples/benchmarks/output/full_results.json
./examples/benchmarks/output/leaderboard.json
./examples/benchmarks/output/results_mteb.json
./examples/benchmarks/output/retrieval_result.json
./examples/benchmarks/run_korean_benchmark.py
./examples/kg_generator_demo.py
./examples/method_plugin_template/README.md
./examples/method_plugin_template/pyproject.toml
./examples/method_plugin_template/src/method_plugin_template/__init__.py
./examples/method_plugin_template/src/method_plugin_template/methods.py
./examples/stage_events.jsonl
./examples/usecase/comprehensive_workflow_test.py
./examples/usecase/insurance_eval_dataset.json
./examples/usecase/output/comprehensive_report.html
./examples/usecase/output/evalvault_memory.db
./frontend/.env.example
./frontend/.gitignore
./frontend/Dockerfile
./frontend/README.md
./frontend/e2e/analysis-compare.spec.ts
./frontend/e2e/analysis-lab.spec.ts
./frontend/e2e/compare-runs.spec.ts
./frontend/e2e/dashboard.spec.ts
./frontend/e2e/domain-memory.spec.ts
./frontend/e2e/evaluation-studio.spec.ts
./frontend/e2e/judge-calibration.spec.ts
./frontend/e2e/knowledge-base.spec.ts
./frontend/e2e/mocks/intents.json
./frontend/e2e/mocks/run_details.json
./frontend/e2e/mocks/runs.json
./frontend/e2e/run-details.spec.ts
./frontend/eslint.config.js
./frontend/index.html
./frontend/nginx.conf
./frontend/package-lock.json
./frontend/package.json
./frontend/playwright.config.ts
./frontend/public/vite.svg
./frontend/src/App.css
./frontend/src/App.tsx
./frontend/src/assets/react.svg
./frontend/src/components/AnalysisNodeOutputs.tsx
./frontend/src/components/InsightSpacePanel.tsx
./frontend/src/components/Layout.tsx
./frontend/src/components/MarkdownContent.tsx
./frontend/src/components/PrioritySummaryPanel.tsx
./frontend/src/components/SpaceLegend.tsx
./frontend/src/components/SpacePlot2D.tsx
./frontend/src/components/SpacePlot3D.tsx
./frontend/src/components/StatusBadge.tsx
./frontend/src/components/VirtualizedText.tsx
./frontend/src/components/ai-elements/Conversation.tsx
./frontend/src/components/ai-elements/Message.tsx
./frontend/src/components/ai-elements/PromptInput.tsx
./frontend/src/components/ai-elements/Response.tsx
./frontend/src/components/ai-elements/index.ts
./frontend/src/config.ts
./frontend/src/config/ui.ts
./frontend/src/hooks/useInsightSpace.ts
./frontend/src/index.css
./frontend/src/main.tsx
./frontend/src/pages/AnalysisCompareView.tsx
./frontend/src/pages/AnalysisLab.tsx
./frontend/src/pages/AnalysisResultView.tsx
./frontend/src/pages/Chat.tsx
./frontend/src/pages/CompareRuns.tsx
./frontend/src/pages/ComprehensiveAnalysis.tsx
./frontend/src/pages/CustomerReport.tsx
./frontend/src/pages/Dashboard.tsx
./frontend/src/pages/DomainMemory.tsx
./frontend/src/pages/EvaluationStudio.tsx
./frontend/src/pages/JudgeCalibration.tsx
./frontend/src/pages/KnowledgeBase.tsx
./frontend/src/pages/RunDetails.tsx
./frontend/src/pages/Settings.tsx
./frontend/src/pages/Visualization.tsx
./frontend/src/pages/VisualizationHome.tsx
./frontend/src/services/api.ts
./frontend/src/types/plotly.d.ts
./frontend/src/utils/format.ts
./frontend/src/utils/phoenix.ts
./frontend/src/utils/runAnalytics.ts
./frontend/src/utils/score.ts
./frontend/src/utils/summaryMetrics.ts
./frontend/tailwind.config.js
./frontend/tsconfig.app.json
./frontend/tsconfig.json
./frontend/tsconfig.node.json
./frontend/vite.config.ts
./htmlcov/.gitignore
./htmlcov/class_index.html
./htmlcov/coverage_html_cb_6fb7b396.js
./htmlcov/coverage_html_cb_bcae5fc4.js
./htmlcov/favicon_32_cb_58284776.png
./htmlcov/function_index.html
./htmlcov/index.html
./htmlcov/keybd_closed_cb_ce680311.png
./htmlcov/status.json
./htmlcov/style_cb_6b508a39.css
./htmlcov/style_cb_a5a05ca4.css
./htmlcov/z_09a1eb8e6cbe5399___init___py.html
./htmlcov/z_09a1eb8e6cbe5399_base_sql_py.html
./htmlcov/z_09a1eb8e6cbe5399_postgres_adapter_py.html
./htmlcov/z_09a1eb8e6cbe5399_sqlite_adapter_py.html
./htmlcov/z_15d0c774bcdd6bac___init___py.html
./htmlcov/z_1896f08e1d9da1ef___init___py.html
./htmlcov/z_1896f08e1d9da1ef_bm25_retriever_py.html
./htmlcov/z_1896f08e1d9da1ef_dense_retriever_py.html
./htmlcov/z_1896f08e1d9da1ef_document_chunker_py.html
./htmlcov/z_1896f08e1d9da1ef_hybrid_retriever_py.html
./htmlcov/z_1896f08e1d9da1ef_kiwi_tokenizer_py.html
./htmlcov/z_1896f08e1d9da1ef_korean_evaluation_py.html
./htmlcov/z_1896f08e1d9da1ef_korean_stopwords_py.html
./htmlcov/z_1896f08e1d9da1ef_toolkit_py.html
./htmlcov/z_19002617e05dff76___init___py.html
./htmlcov/z_19002617e05dff76_agent_py.html
./htmlcov/z_19002617e05dff76_analyze_py.html
./htmlcov/z_19002617e05dff76_benchmark_py.html
./htmlcov/z_19002617e05dff76_config_py.html
./htmlcov/z_19002617e05dff76_domain_py.html
./htmlcov/z_19002617e05dff76_experiment_py.html
./htmlcov/z_19002617e05dff76_gate_py.html
./htmlcov/z_19002617e05dff76_generate_py.html
./htmlcov/z_19002617e05dff76_history_py.html
./htmlcov/z_19002617e05dff76_kg_py.html
./htmlcov/z_19002617e05dff76_langfuse_py.html
./htmlcov/z_19002617e05dff76_pipeline_py.html
./htmlcov/z_19002617e05dff76_run_py.html
./htmlcov/z_19002617e05dff76_web_py.html
./htmlcov/z_20c6c1d02076900c___init___py.html
./htmlcov/z_20c6c1d02076900c_theme_py.html
./htmlcov/z_2d56cdefe429235e___init___py.html
./htmlcov/z_2d56cdefe429235e_cards_py.html
./htmlcov/z_2d56cdefe429235e_charts_py.html
./htmlcov/z_2d56cdefe429235e_evaluate_py.html
./htmlcov/z_2d56cdefe429235e_history_py.html
./htmlcov/z_2d56cdefe429235e_lists_py.html
./htmlcov/z_2d56cdefe429235e_metrics_py.html
./htmlcov/z_2d56cdefe429235e_progress_py.html
./htmlcov/z_2d56cdefe429235e_reports_py.html
./htmlcov/z_2d56cdefe429235e_stats_py.html
./htmlcov/z_2d56cdefe429235e_upload_py.html
./htmlcov/z_307c0430633cfe24___init___py.html
./htmlcov/z_307c0430633cfe24_insight_generator_py.html
./htmlcov/z_307c0430633cfe24_pattern_detector_py.html
./htmlcov/z_307c0430633cfe24_playbook_loader_py.html
./htmlcov/z_354ee341f7b1ed39___init___py.html
./htmlcov/z_354ee341f7b1ed39_sqlite_adapter_py.html
./htmlcov/z_45fd31b21b5db4a9___init___py.html
./htmlcov/z_45fd31b21b5db4a9_llm_report_generator_py.html
./htmlcov/z_45fd31b21b5db4a9_markdown_adapter_py.html
./htmlcov/z_4c03e7fdb49adcce___init___py.html
./htmlcov/z_4c03e7fdb49adcce_cli_py.html
./htmlcov/z_6ef5e8a36594507c___init___py.html
./htmlcov/z_6ef5e8a36594507c_analysis_pipeline_py.html
./htmlcov/z_6ef5e8a36594507c_analysis_py.html
./htmlcov/z_6ef5e8a36594507c_benchmark_py.html
./htmlcov/z_6ef5e8a36594507c_dataset_py.html
./htmlcov/z_6ef5e8a36594507c_experiment_py.html
./htmlcov/z_6ef5e8a36594507c_improvement_py.html
./htmlcov/z_6ef5e8a36594507c_kg_py.html
./htmlcov/z_6ef5e8a36594507c_memory_py.html
./htmlcov/z_6ef5e8a36594507c_rag_trace_py.html
./htmlcov/z_6ef5e8a36594507c_result_py.html
./htmlcov/z_706276de613709ef___init___py.html
./htmlcov/z_706276de613709ef_anthropic_adapter_py.html
./htmlcov/z_706276de613709ef_azure_adapter_py.html
./htmlcov/z_706276de613709ef_base_py.html
./htmlcov/z_706276de613709ef_llm_relation_augmenter_py.html
./htmlcov/z_706276de613709ef_ollama_adapter_py.html
./htmlcov/z_706276de613709ef_openai_adapter_py.html
./htmlcov/z_706276de613709ef_token_aware_chat_py.html
./htmlcov/z_8ab9a5c51a8689a0___init___py.html
./htmlcov/z_8ab9a5c51a8689a0_analysis_service_py.html
./htmlcov/z_8ab9a5c51a8689a0_batch_executor_py.html
./htmlcov/z_8ab9a5c51a8689a0_benchmark_runner_py.html
./htmlcov/z_8ab9a5c51a8689a0_document_chunker_py.html
./htmlcov/z_8ab9a5c51a8689a0_domain_learning_hook_py.html
./htmlcov/z_8ab9a5c51a8689a0_entity_extractor_py.html
./htmlcov/z_8ab9a5c51a8689a0_evaluator_py.html
./htmlcov/z_8ab9a5c51a8689a0_experiment_manager_py.html
./htmlcov/z_8ab9a5c51a8689a0_improvement_guide_service_py.html
./htmlcov/z_8ab9a5c51a8689a0_intent_classifier_py.html
./htmlcov/z_8ab9a5c51a8689a0_kg_generator_py.html
./htmlcov/z_8ab9a5c51a8689a0_memory_aware_evaluator_py.html
./htmlcov/z_8ab9a5c51a8689a0_memory_based_analysis_py.html
./htmlcov/z_8ab9a5c51a8689a0_pipeline_orchestrator_py.html
./htmlcov/z_8ab9a5c51a8689a0_pipeline_template_registry_py.html
./htmlcov/z_8ab9a5c51a8689a0_testset_generator_py.html
./htmlcov/z_8f8456551edf1193___init___py.html
./htmlcov/z_9c2203071244a422___init___py.html
./htmlcov/z_ae47c9b820c840f4___init___py.html
./htmlcov/z_ae47c9b820c840f4_langfuse_adapter_py.html
./htmlcov/z_ae47c9b820c840f4_mlflow_adapter_py.html
./htmlcov/z_ae47c9b820c840f4_phoenix_adapter_py.html
./htmlcov/z_af18d2f1810e66bd___init___py.html
./htmlcov/z_b8ea285b79335352___init___py.html
./htmlcov/z_b8ea285b79335352_formatters_py.html
./htmlcov/z_b8ea285b79335352_options_py.html
./htmlcov/z_b8ea285b79335352_validators_py.html
./htmlcov/z_bf0ff448b6346c7b___init___py.html
./htmlcov/z_bf0ff448b6346c7b_adapter_py.html
./htmlcov/z_bf0ff448b6346c7b_app_py.html
./htmlcov/z_bf0ff448b6346c7b_session_py.html
./htmlcov/z_c503ad3c05f061fe___init___py.html
./htmlcov/z_c60a5984f1f262ae___init___py.html
./htmlcov/z_c60a5984f1f262ae_memory_cache_py.html
./htmlcov/z_cf913e7f461137cc___init___py.html
./htmlcov/z_d5db758984fd2c73___init___py.html
./htmlcov/z_d5db758984fd2c73_app_py.html
./htmlcov/z_d7401fdcbfb3676e___init___py.html
./htmlcov/z_dc78805f3d415bd4___init___py.html
./htmlcov/z_dc78805f3d415bd4_agent_types_py.html
./htmlcov/z_dc78805f3d415bd4_domain_config_py.html
./htmlcov/z_dc78805f3d415bd4_instrumentation_py.html
./htmlcov/z_dc78805f3d415bd4_model_config_py.html
./htmlcov/z_dc78805f3d415bd4_settings_py.html
./htmlcov/z_dd9f472a22bdd3cb___init___py.html
./htmlcov/z_dd9f472a22bdd3cb_analysis_cache_port_py.html
./htmlcov/z_dd9f472a22bdd3cb_analysis_module_port_py.html
./htmlcov/z_dd9f472a22bdd3cb_analysis_port_py.html
./htmlcov/z_dd9f472a22bdd3cb_causal_analysis_port_py.html
./htmlcov/z_dd9f472a22bdd3cb_dataset_port_py.html
./htmlcov/z_dd9f472a22bdd3cb_domain_memory_port_py.html
./htmlcov/z_dd9f472a22bdd3cb_embedding_port_py.html
./htmlcov/z_dd9f472a22bdd3cb_improvement_port_py.html
./htmlcov/z_dd9f472a22bdd3cb_intent_classifier_port_py.html
./htmlcov/z_dd9f472a22bdd3cb_korean_nlp_port_py.html
./htmlcov/z_dd9f472a22bdd3cb_llm_port_py.html
./htmlcov/z_dd9f472a22bdd3cb_nlp_analysis_port_py.html
./htmlcov/z_dd9f472a22bdd3cb_relation_augmenter_port_py.html
./htmlcov/z_dd9f472a22bdd3cb_report_port_py.html
./htmlcov/z_dd9f472a22bdd3cb_storage_port_py.html
./htmlcov/z_dd9f472a22bdd3cb_tracker_port_py.html
./htmlcov/z_eed2f4e786e833c2___init___py.html
./htmlcov/z_eed2f4e786e833c2_analysis_pipeline_port_py.html
./htmlcov/z_eed2f4e786e833c2_evaluator_port_py.html
./htmlcov/z_eed2f4e786e833c2_learning_hook_port_py.html
./htmlcov/z_eed2f4e786e833c2_web_port_py.html
./htmlcov/z_f2babf63a4f78925___init___py.html
./htmlcov/z_f2babf63a4f78925_analysis_report_module_py.html
./htmlcov/z_f2babf63a4f78925_base_module_py.html
./htmlcov/z_f2babf63a4f78925_causal_adapter_py.html
./htmlcov/z_f2babf63a4f78925_causal_analyzer_module_py.html
./htmlcov/z_f2babf63a4f78925_common_py.html
./htmlcov/z_f2babf63a4f78925_comparison_report_module_py.html
./htmlcov/z_f2babf63a4f78925_data_loader_module_py.html
./htmlcov/z_f2babf63a4f78925_nlp_adapter_py.html
./htmlcov/z_f2babf63a4f78925_nlp_analyzer_module_py.html
./htmlcov/z_f2babf63a4f78925_statistical_adapter_py.html
./htmlcov/z_f2babf63a4f78925_statistical_analyzer_module_py.html
./htmlcov/z_f2babf63a4f78925_summary_report_module_py.html
./htmlcov/z_f2babf63a4f78925_verification_report_module_py.html
./htmlcov/z_f850069011182385___init___py.html
./htmlcov/z_f850069011182385_insurance_py.html
./htmlcov/z_ff13382c39ff3e3e___init___py.html
./htmlcov/z_ff13382c39ff3e3e_base_py.html
./htmlcov/z_ff13382c39ff3e3e_csv_loader_py.html
./htmlcov/z_ff13382c39ff3e3e_excel_loader_py.html
./htmlcov/z_ff13382c39ff3e3e_json_loader_py.html
./htmlcov/z_ff13382c39ff3e3e_loader_factory_py.html
./mkdocs.yml
./package-lock.json
./prompts/system_override.txt
./pyproject.toml
./reports/.gitkeep
./reports/README.md
./reports/analysis/analysis_0aa9fab0-6c2c-4c1c-b228-202a38a2f00c.json
./reports/analysis/analysis_0aa9fab0-6c2c-4c1c-b228-202a38a2f00c.md
./reports/analysis/analysis_2163f844-ee2c-4630-9ba8-35cd9954d92e.json
./reports/analysis/analysis_2163f844-ee2c-4630-9ba8-35cd9954d92e.md
./reports/analysis/analysis_4516d358-2797-4c46-9f14-c1d975588025.json
./reports/analysis/analysis_4516d358-2797-4c46-9f14-c1d975588025.md
./reports/analysis/analysis_4792d785-a8ea-4fd3-8a0c-dcbf1889f5fb.json
./reports/analysis/analysis_4792d785-a8ea-4fd3-8a0c-dcbf1889f5fb.md
./reports/analysis/analysis_8f825b22-87f1-4d9b-b3a0-8ff65dbec2c5.json
./reports/analysis/analysis_8f825b22-87f1-4d9b-b3a0-8ff65dbec2c5.md
./reports/analysis/analysis_9fbf4776-9f5b-4c4b-ba08-c556032cee86.json
./reports/analysis/analysis_9fbf4776-9f5b-4c4b-ba08-c556032cee86.md
./reports/analysis/analysis_e2f7e6bb-a86e-4f6a-8002-0c6f1a831775.json
./reports/analysis/analysis_e2f7e6bb-a86e-4f6a-8002-0c6f1a831775.md
./reports/analysis/analysis_f1287e90-43b6-42c8-b3ac-e6cb3e06a71e.json
./reports/analysis/analysis_f1287e90-43b6-42c8-b3ac-e6cb3e06a71e.md
./reports/analysis/artifacts/analysis_4516d358-2797-4c46-9f14-c1d975588025/causal_analysis.json
./reports/analysis/artifacts/analysis_4516d358-2797-4c46-9f14-c1d975588025/diagnostic.json
./reports/analysis/artifacts/analysis_4516d358-2797-4c46-9f14-c1d975588025/final_output.json
./reports/analysis/artifacts/analysis_4516d358-2797-4c46-9f14-c1d975588025/index.json
./reports/analysis/artifacts/analysis_4516d358-2797-4c46-9f14-c1d975588025/load_data.json
./reports/analysis/artifacts/analysis_4516d358-2797-4c46-9f14-c1d975588025/load_runs.json
./reports/analysis/artifacts/analysis_4516d358-2797-4c46-9f14-c1d975588025/low_samples.json
./reports/analysis/artifacts/analysis_4516d358-2797-4c46-9f14-c1d975588025/nlp_analysis.json
./reports/analysis/artifacts/analysis_4516d358-2797-4c46-9f14-c1d975588025/pattern_detection.json
./reports/analysis/artifacts/analysis_4516d358-2797-4c46-9f14-c1d975588025/priority_summary.json
./reports/analysis/artifacts/analysis_4516d358-2797-4c46-9f14-c1d975588025/ragas_eval.json
./reports/analysis/artifacts/analysis_4516d358-2797-4c46-9f14-c1d975588025/report.json
./reports/analysis/artifacts/analysis_4516d358-2797-4c46-9f14-c1d975588025/root_cause.json
./reports/analysis/artifacts/analysis_4516d358-2797-4c46-9f14-c1d975588025/statistics.json
./reports/analysis/artifacts/analysis_4516d358-2797-4c46-9f14-c1d975588025/time_series.json
./reports/analysis/artifacts/analysis_4516d358-2797-4c46-9f14-c1d975588025/trend_detection.json
./reports/analysis/artifacts/analysis_4792d785-a8ea-4fd3-8a0c-dcbf1889f5fb/causal_analysis.json
./reports/analysis/artifacts/analysis_4792d785-a8ea-4fd3-8a0c-dcbf1889f5fb/diagnostic.json
./reports/analysis/artifacts/analysis_4792d785-a8ea-4fd3-8a0c-dcbf1889f5fb/final_output.json
./reports/analysis/artifacts/analysis_4792d785-a8ea-4fd3-8a0c-dcbf1889f5fb/index.json
./reports/analysis/artifacts/analysis_4792d785-a8ea-4fd3-8a0c-dcbf1889f5fb/load_data.json
./reports/analysis/artifacts/analysis_4792d785-a8ea-4fd3-8a0c-dcbf1889f5fb/load_runs.json
./reports/analysis/artifacts/analysis_4792d785-a8ea-4fd3-8a0c-dcbf1889f5fb/low_samples.json
./reports/analysis/artifacts/analysis_4792d785-a8ea-4fd3-8a0c-dcbf1889f5fb/nlp_analysis.json
./reports/analysis/artifacts/analysis_4792d785-a8ea-4fd3-8a0c-dcbf1889f5fb/pattern_detection.json
./reports/analysis/artifacts/analysis_4792d785-a8ea-4fd3-8a0c-dcbf1889f5fb/priority_summary.json
./reports/analysis/artifacts/analysis_4792d785-a8ea-4fd3-8a0c-dcbf1889f5fb/ragas_eval.json
./reports/analysis/artifacts/analysis_4792d785-a8ea-4fd3-8a0c-dcbf1889f5fb/report.json
./reports/analysis/artifacts/analysis_4792d785-a8ea-4fd3-8a0c-dcbf1889f5fb/root_cause.json
./reports/analysis/artifacts/analysis_4792d785-a8ea-4fd3-8a0c-dcbf1889f5fb/statistics.json
./reports/analysis/artifacts/analysis_4792d785-a8ea-4fd3-8a0c-dcbf1889f5fb/time_series.json
./reports/analysis/artifacts/analysis_4792d785-a8ea-4fd3-8a0c-dcbf1889f5fb/trend_detection.json
./reports/analysis/artifacts/analysis_8f825b22-87f1-4d9b-b3a0-8ff65dbec2c5/causal_analysis.json
./reports/analysis/artifacts/analysis_8f825b22-87f1-4d9b-b3a0-8ff65dbec2c5/diagnostic.json
./reports/analysis/artifacts/analysis_8f825b22-87f1-4d9b-b3a0-8ff65dbec2c5/final_output.json
./reports/analysis/artifacts/analysis_8f825b22-87f1-4d9b-b3a0-8ff65dbec2c5/index.json
./reports/analysis/artifacts/analysis_8f825b22-87f1-4d9b-b3a0-8ff65dbec2c5/load_data.json
./reports/analysis/artifacts/analysis_8f825b22-87f1-4d9b-b3a0-8ff65dbec2c5/load_runs.json
./reports/analysis/artifacts/analysis_8f825b22-87f1-4d9b-b3a0-8ff65dbec2c5/low_samples.json
./reports/analysis/artifacts/analysis_8f825b22-87f1-4d9b-b3a0-8ff65dbec2c5/nlp_analysis.json
./reports/analysis/artifacts/analysis_8f825b22-87f1-4d9b-b3a0-8ff65dbec2c5/pattern_detection.json
./reports/analysis/artifacts/analysis_8f825b22-87f1-4d9b-b3a0-8ff65dbec2c5/priority_summary.json
./reports/analysis/artifacts/analysis_8f825b22-87f1-4d9b-b3a0-8ff65dbec2c5/ragas_eval.json
./reports/analysis/artifacts/analysis_8f825b22-87f1-4d9b-b3a0-8ff65dbec2c5/report.json
./reports/analysis/artifacts/analysis_8f825b22-87f1-4d9b-b3a0-8ff65dbec2c5/root_cause.json
./reports/analysis/artifacts/analysis_8f825b22-87f1-4d9b-b3a0-8ff65dbec2c5/statistics.json
./reports/analysis/artifacts/analysis_8f825b22-87f1-4d9b-b3a0-8ff65dbec2c5/time_series.json
./reports/analysis/artifacts/analysis_8f825b22-87f1-4d9b-b3a0-8ff65dbec2c5/trend_detection.json
./reports/analysis/artifacts/analysis_e2f7e6bb-a86e-4f6a-8002-0c6f1a831775/causal_analysis.json
./reports/analysis/artifacts/analysis_e2f7e6bb-a86e-4f6a-8002-0c6f1a831775/diagnostic.json
./reports/analysis/artifacts/analysis_e2f7e6bb-a86e-4f6a-8002-0c6f1a831775/final_output.json
./reports/analysis/artifacts/analysis_e2f7e6bb-a86e-4f6a-8002-0c6f1a831775/index.json
./reports/analysis/artifacts/analysis_e2f7e6bb-a86e-4f6a-8002-0c6f1a831775/load_data.json
./reports/analysis/artifacts/analysis_e2f7e6bb-a86e-4f6a-8002-0c6f1a831775/load_runs.json
./reports/analysis/artifacts/analysis_e2f7e6bb-a86e-4f6a-8002-0c6f1a831775/low_samples.json
./reports/analysis/artifacts/analysis_e2f7e6bb-a86e-4f6a-8002-0c6f1a831775/nlp_analysis.json
./reports/analysis/artifacts/analysis_e2f7e6bb-a86e-4f6a-8002-0c6f1a831775/pattern_detection.json
./reports/analysis/artifacts/analysis_e2f7e6bb-a86e-4f6a-8002-0c6f1a831775/priority_summary.json
./reports/analysis/artifacts/analysis_e2f7e6bb-a86e-4f6a-8002-0c6f1a831775/ragas_eval.json
./reports/analysis/artifacts/analysis_e2f7e6bb-a86e-4f6a-8002-0c6f1a831775/report.json
./reports/analysis/artifacts/analysis_e2f7e6bb-a86e-4f6a-8002-0c6f1a831775/root_cause.json
./reports/analysis/artifacts/analysis_e2f7e6bb-a86e-4f6a-8002-0c6f1a831775/statistics.json
./reports/analysis/artifacts/analysis_e2f7e6bb-a86e-4f6a-8002-0c6f1a831775/time_series.json
./reports/analysis/artifacts/analysis_e2f7e6bb-a86e-4f6a-8002-0c6f1a831775/trend_detection.json
./reports/analysis/artifacts/analysis_f1287e90-43b6-42c8-b3ac-e6cb3e06a71e/causal_analysis.json
./reports/analysis/artifacts/analysis_f1287e90-43b6-42c8-b3ac-e6cb3e06a71e/diagnostic.json
./reports/analysis/artifacts/analysis_f1287e90-43b6-42c8-b3ac-e6cb3e06a71e/final_output.json
./reports/analysis/artifacts/analysis_f1287e90-43b6-42c8-b3ac-e6cb3e06a71e/index.json
./reports/analysis/artifacts/analysis_f1287e90-43b6-42c8-b3ac-e6cb3e06a71e/load_data.json
./reports/analysis/artifacts/analysis_f1287e90-43b6-42c8-b3ac-e6cb3e06a71e/load_runs.json
./reports/analysis/artifacts/analysis_f1287e90-43b6-42c8-b3ac-e6cb3e06a71e/low_samples.json
./reports/analysis/artifacts/analysis_f1287e90-43b6-42c8-b3ac-e6cb3e06a71e/nlp_analysis.json
./reports/analysis/artifacts/analysis_f1287e90-43b6-42c8-b3ac-e6cb3e06a71e/pattern_detection.json
./reports/analysis/artifacts/analysis_f1287e90-43b6-42c8-b3ac-e6cb3e06a71e/priority_summary.json
./reports/analysis/artifacts/analysis_f1287e90-43b6-42c8-b3ac-e6cb3e06a71e/ragas_eval.json
./reports/analysis/artifacts/analysis_f1287e90-43b6-42c8-b3ac-e6cb3e06a71e/report.json
./reports/analysis/artifacts/analysis_f1287e90-43b6-42c8-b3ac-e6cb3e06a71e/root_cause.json
./reports/analysis/artifacts/analysis_f1287e90-43b6-42c8-b3ac-e6cb3e06a71e/statistics.json
./reports/analysis/artifacts/analysis_f1287e90-43b6-42c8-b3ac-e6cb3e06a71e/time_series.json
./reports/analysis/artifacts/analysis_f1287e90-43b6-42c8-b3ac-e6cb3e06a71e/trend_detection.json
./reports/comparison/artifacts/comparison_0aa9fab0_f1287e90/final_output.json
./reports/comparison/artifacts/comparison_0aa9fab0_f1287e90/index.json
./reports/comparison/artifacts/comparison_0aa9fab0_f1287e90/load_runs.json
./reports/comparison/artifacts/comparison_0aa9fab0_f1287e90/report.json
./reports/comparison/artifacts/comparison_0aa9fab0_f1287e90/run_change_detection.json
./reports/comparison/artifacts/comparison_0aa9fab0_f1287e90/run_metric_comparison.json
./reports/comparison/artifacts/comparison_8f825b22_4516d358/final_output.json
./reports/comparison/artifacts/comparison_8f825b22_4516d358/index.json
./reports/comparison/artifacts/comparison_8f825b22_4516d358/load_runs.json
./reports/comparison/artifacts/comparison_8f825b22_4516d358/report.json
./reports/comparison/artifacts/comparison_8f825b22_4516d358/run_change_detection.json
./reports/comparison/artifacts/comparison_8f825b22_4516d358/run_metric_comparison.json
./reports/comparison/artifacts/comparison_f1287e90_8f825b22/final_output.json
./reports/comparison/artifacts/comparison_f1287e90_8f825b22/index.json
./reports/comparison/artifacts/comparison_f1287e90_8f825b22/load_runs.json
./reports/comparison/artifacts/comparison_f1287e90_8f825b22/report.json
./reports/comparison/artifacts/comparison_f1287e90_8f825b22/run_change_detection.json
./reports/comparison/artifacts/comparison_f1287e90_8f825b22/run_metric_comparison.json
./reports/comparison/artifacts/comparison_run-1_run-2/final_output.json
./reports/comparison/artifacts/comparison_run-1_run-2/index.json
./reports/comparison/comparison_0aa9fab0_9fbf4776.json
./reports/comparison/comparison_0aa9fab0_9fbf4776.md
./reports/comparison/comparison_0aa9fab0_f1287e90.json
./reports/comparison/comparison_0aa9fab0_f1287e90.md
./reports/comparison/comparison_8f825b22_4516d358.json
./reports/comparison/comparison_8f825b22_4516d358.md
./reports/comparison/comparison_9fbf4776_a491fa0e.json
./reports/comparison/comparison_9fbf4776_a491fa0e.md
./reports/comparison/comparison_f1287e90_8f825b22.json
./reports/comparison/comparison_f1287e90_8f825b22.md
./reports/comparison/comparison_run-1_run-2.json
./reports/comparison/comparison_run-1_run-2.md
./reports/debug_report_r1_smoke.md
./reports/debug_report_r2_graphrag.md
./reports/debug_report_r2_graphrag_openai.md
./reports/debug_report_r3_bm25.md
./reports/debug_report_r3_bm25_langfuse3.md
./reports/debug_report_r3_dense_faiss.md
./reports/feature_verification_report.md
./reports/graphrag_compare.json
./reports/graphrag_compare_qwen3_14b.json
./reports/graphrag_compare_qwen3_14b_multi_faithfulness.json
./reports/improvement_1d91a667-4288-4742-be3a-a8f5310c5140.md
./reports/presentation_materials_final.md
./reports/presentation_materials_phase1.md
./reports/presentation_materials_phase2.md
./reports/presentation_materials_verification.md
./reports/r2_graphrag_openai_stage_events.jsonl
./reports/r2_graphrag_openai_stage_report.txt
./reports/r2_graphrag_stage_events.jsonl
./reports/r2_graphrag_stage_report.txt
./reports/r3_bm25_langfuse2_stage_events.jsonl
./reports/r3_bm25_langfuse3_stage_events.jsonl
./reports/r3_bm25_langfuse_stage_events.jsonl
./reports/r3_bm25_phoenix_stage_events.jsonl
./reports/r3_bm25_stage_events.jsonl
./reports/r3_bm25_stage_report.txt
./reports/r3_dense_faiss_stage_events.jsonl
./reports/r3_dense_faiss_stage_report.txt
./reports/ralph_loop_briefing.md
./reports/retrieval_benchmark_smoke_precision.csv
./reports/retrieval_benchmark_smoke_precision_graphrag.csv
./reports/retrieval_benchmark_smoke_precision_multi.csv
./scratch/api.log
./scratch/frontend.log
./scratch/r1_smoke/dataset.json
./scratch/r1_smoke/evalvault.db
./scratch/r1_smoke/prompt.txt
./scratch/r1_smoke/prompt_manifest.json
./scratch/r1_smoke/run.json
./scratch/r1_smoke/run.log
./scratch/r1_smoke/stage_events.jsonl
./scratch/r1_smoke/stage_report.txt
./scratch/ragrefine/__init__.py
./scratch/ragrefine/agent/__init__.py
./scratch/ragrefine/agent/agent_manager.py
./scratch/ragrefine/agent/api.py
./scratch/ragrefine/agent/cli.py
./scratch/ragrefine/agent/events.py
./scratch/ragrefine/agent/graph.py
./scratch/ragrefine/agent/professional_prompts.py
./scratch/ragrefine/agent/session.py
./scratch/ragrefine/agent/tools/__init__.py
./scratch/ragrefine/agent/tools/advanced_smart_chat_tools.py
./scratch/ragrefine/agent/tools/analysis_data_tools.py
./scratch/ragrefine/agent/tools/analysis_tools.py
./scratch/ragrefine/agent/tools/auto_source_analyst.py
./scratch/ragrefine/agent/tools/comparison_tools.py
./scratch/ragrefine/agent/tools/file_tools.py
./scratch/ragrefine/agent/tools/lightweight_tools.py
./scratch/ragrefine/agent/tools/metadata.py
./scratch/ragrefine/agent/tools/multi_intent_analyst.py
./scratch/ragrefine/agent/tools/simple_payload_reader.py
./scratch/ragrefine/agent/tools/smart_analyst_tools.py
./scratch/ragrefine/agent/tools/smart_chat_tools.py
./scratch/ragrefine/analysis/__init__.py
./scratch/ragrefine/analysis/advanced_ragas.py
./scratch/ragrefine/analysis/bandit_optimizer.py
./scratch/ragrefine/analysis/bayesian_ab_test.py
./scratch/ragrefine/analysis/causal_analysis.py
./scratch/ragrefine/analysis/causal_reasoning_engine.py
./scratch/ragrefine/analysis/comprehensive_report_generator.py
./scratch/ragrefine/analysis/context_semantic_analyzer.py
./scratch/ragrefine/analysis/data_pipeline.py
./scratch/ragrefine/analysis/dataset_profiler.py
./scratch/ragrefine/analysis/deepeval_evaluator.py
./scratch/ragrefine/analysis/diagnostic_playbook.py
./scratch/ragrefine/analysis/file_schema.py
./scratch/ragrefine/analysis/hcx_client.py
./scratch/ragrefine/analysis/io.py
./scratch/ragrefine/analysis/keybert_analyzer.py
./scratch/ragrefine/analysis/llm_evaluation.py
./scratch/ragrefine/analysis/llm_service.py
./scratch/ragrefine/analysis/locale_utils.py
./scratch/ragrefine/analysis/meta_analyzer.py
./scratch/ragrefine/analysis/meta_reviewer.py
./scratch/ragrefine/analysis/network_graph_analyzer.py
./scratch/ragrefine/analysis/prompt_analysis.py
./scratch/ragrefine/analysis/question_analysis.py
./scratch/ragrefine/analysis/question_type_classifier.py
./scratch/ragrefine/analysis/ragas_extensions.py
./scratch/ragrefine/analysis/report/__init__.py
./scratch/ragrefine/analysis/report/base_generator.py
./scratch/ragrefine/analysis/report_generator.py
./scratch/ragrefine/analysis/report_graph.py
./scratch/ragrefine/analysis/report_schema.py
./scratch/ragrefine/analysis/report_utils.py
./scratch/ragrefine/analysis/result_loader.py
./scratch/ragrefine/analysis/temporal_analysis.py
./scratch/ragrefine/analysis/topic_clustering.py
./scratch/ragrefine/analysis/types.py
./scratch/ragrefine/analysis/user_dictionary_analyzer.py
./scratch/ragrefine/analysis/visualization.py
./scratch/ragrefine/cache/__init__.py
./scratch/ragrefine/cache/analysis_cache.py
./scratch/ragrefine/cache/cache_config.py
./scratch/ragrefine/cli.py
./scratch/ragrefine/data/__init__.py
./scratch/ragrefine/data/quality_validator.py
./scratch/ragrefine/data/synthetic_data_engine.py
./scratch/ragrefine/db/__init__.py
./scratch/ragrefine/db/chat_history.py
./scratch/ragrefine/experiments/__init__.py
./scratch/ragrefine/experiments/comparison_engine.py
./scratch/ragrefine/experiments/experiment_tracker.py
./scratch/ragrefine/langgraph_report_generator.py
./scratch/ragrefine/logging_config.py
./scratch/ragrefine/rag_expert_synth/__init__.py
./scratch/ragrefine/rag_expert_synth/cli.py
./scratch/ragrefine/rag_expert_synth/combiner.py
./scratch/ragrefine/rag_expert_synth/evidence.py
./scratch/ragrefine/rag_expert_synth/exceptions.py
./scratch/ragrefine/rag_expert_synth/fuzzy_rules.py
./scratch/ragrefine/rag_expert_synth/renderer.py
./scratch/ragrefine/rag_expert_synth/rules.py
./scratch/ragrefine/rag_expert_synth/templates/base_report.md.j2
./scratch/ragrefine/rag_expert_synth/types.py
./scratch/ragrefine/utils/chat_data_reader.py
./scratch/ragrefine/utils/chat_insights_generator.py
./scratch/ragrefine/utils/intelligent_data_retriever.py
./scratch/summary_eval_smoke_2.json
./scratch/summary_eval_smoke_3.json
./scratch/summary_eval_smoke_3_insurance.json
./scripts/benchmark/download_kmmlu.py
./scripts/ci/run_regression_gate.py
./scripts/dev/open_rag_trace_demo.py
./scripts/dev/open_rag_trace_integration_template.py
./scripts/dev/otel-collector-config.yaml
./scripts/dev/start_web_ui_with_phoenix.sh
./scripts/dev/validate_open_rag_trace.py
./scripts/dev/verify_dashboard_endpoint.sh
./scripts/dev_seed_pipeline_results.py
./scripts/docs/__init__.py
./scripts/docs/analyzer/__init__.py
./scripts/docs/analyzer/ast_scanner.py
./scripts/docs/analyzer/confidence_scorer.py
./scripts/docs/analyzer/graph_builder.py
./scripts/docs/analyzer/side_effect_detector.py
./scripts/docs/generate_api_docs.py
./scripts/docs/models/__init__.py
./scripts/docs/models/schema.py
./scripts/docs/renderer/__init__.py
./scripts/docs/renderer/html_generator.py
./scripts/offline/bundle_datasets.sh
./scripts/offline/export_images.sh
./scripts/offline/import_images.sh
./scripts/offline/restore_datasets.sh
./scripts/offline/smoke_test.sh
./scripts/ops/phoenix_watch.py
./scripts/perf/backfill_langfuse_trace_url.py
./scripts/perf/r3_dense_smoke.py
./scripts/perf/r3_evalvault_run_dataset.json
./scripts/perf/r3_retriever_docs.json
./scripts/perf/r3_smoke_real.jsonl
./scripts/perf/r3_stage_events_sample.jsonl
./scripts/pipeline_template_inspect.py
./scripts/reports/generate_release_notes.py
./scripts/run_with_timeout.py
./scripts/test_full_evaluation.py
./scripts/tests/run_regressions.py
./scripts/tests/run_retriever_stage_report_smoke.sh
./scripts/validate_tutorials.py
./scripts/verify_ragas_compliance.py
./scripts/verify_workflows.py
./site/404.html
./site/ANALYSIS_IMPROVEMENT_PLAN/index.html
./site/INDEX/index.html
./site/README.ko/index.html
./site/ROADMAP/index.html
./site/STATUS/index.html
./site/api/adapters/inbound/index.html
./site/api/adapters/outbound/index.html
./site/api/config/index.html
./site/api/domain/entities/index.html
./site/api/domain/metrics/index.html
./site/api/domain/services/index.html
./site/api/ports/inbound/index.html
./site/api/ports/outbound/index.html
./site/architecture/open-rag-trace-collector/index.html
./site/architecture/open-rag-trace-spec/index.html
./site/assets/_mkdocstrings.css
./site/assets/images/favicon.png
./site/assets/javascripts/bundle.79ae519e.min.js
./site/assets/javascripts/bundle.79ae519e.min.js.map
./site/assets/javascripts/lunr/min/lunr.ar.min.js
./site/assets/javascripts/lunr/min/lunr.da.min.js
./site/assets/javascripts/lunr/min/lunr.de.min.js
./site/assets/javascripts/lunr/min/lunr.du.min.js
./site/assets/javascripts/lunr/min/lunr.el.min.js
./site/assets/javascripts/lunr/min/lunr.es.min.js
./site/assets/javascripts/lunr/min/lunr.fi.min.js
./site/assets/javascripts/lunr/min/lunr.fr.min.js
./site/assets/javascripts/lunr/min/lunr.he.min.js
./site/assets/javascripts/lunr/min/lunr.hi.min.js
./site/assets/javascripts/lunr/min/lunr.hu.min.js
./site/assets/javascripts/lunr/min/lunr.hy.min.js
./site/assets/javascripts/lunr/min/lunr.it.min.js
./site/assets/javascripts/lunr/min/lunr.ja.min.js
./site/assets/javascripts/lunr/min/lunr.jp.min.js
./site/assets/javascripts/lunr/min/lunr.kn.min.js
./site/assets/javascripts/lunr/min/lunr.ko.min.js
./site/assets/javascripts/lunr/min/lunr.multi.min.js
./site/assets/javascripts/lunr/min/lunr.nl.min.js
./site/assets/javascripts/lunr/min/lunr.no.min.js
./site/assets/javascripts/lunr/min/lunr.pt.min.js
./site/assets/javascripts/lunr/min/lunr.ro.min.js
./site/assets/javascripts/lunr/min/lunr.ru.min.js
./site/assets/javascripts/lunr/min/lunr.sa.min.js
./site/assets/javascripts/lunr/min/lunr.stemmer.support.min.js
./site/assets/javascripts/lunr/min/lunr.sv.min.js
./site/assets/javascripts/lunr/min/lunr.ta.min.js
./site/assets/javascripts/lunr/min/lunr.te.min.js
./site/assets/javascripts/lunr/min/lunr.th.min.js
./site/assets/javascripts/lunr/min/lunr.tr.min.js
./site/assets/javascripts/lunr/min/lunr.vi.min.js
./site/assets/javascripts/lunr/min/lunr.zh.min.js
./site/assets/javascripts/lunr/tinyseg.js
./site/assets/javascripts/lunr/wordcut.js
./site/assets/javascripts/workers/search.2c215733.min.js
./site/assets/javascripts/workers/search.2c215733.min.js.map
./site/assets/stylesheets/main.484c7ddc.min.css
./site/assets/stylesheets/main.484c7ddc.min.css.map
./site/assets/stylesheets/palette.ab4e12ef.min.css
./site/assets/stylesheets/palette.ab4e12ef.min.css.map
./site/getting-started/INSTALLATION/index.html
./site/guides/DEV_GUIDE/index.html
./site/guides/RELEASE_CHECKLIST/index.html
./site/guides/USER_GUIDE/index.html
./site/guides/open-rag-trace-internal-adapter/index.html
./site/guides/open-rag-trace-samples/index.html
./site/mapping/component-to-whitepaper.yaml
./site/new_whitepaper/00_frontmatter/index.html
./site/new_whitepaper/01_overview/index.html
./site/new_whitepaper/02_architecture/index.html
./site/new_whitepaper/03_data_flow/index.html
./site/new_whitepaper/04_components/index.html
./site/new_whitepaper/05_expert_lenses/index.html
./site/new_whitepaper/06_implementation/index.html
./site/new_whitepaper/07_advanced/index.html
./site/new_whitepaper/08_customization/index.html
./site/new_whitepaper/09_quality/index.html
./site/new_whitepaper/10_performance/index.html
./site/new_whitepaper/11_security/index.html
./site/new_whitepaper/12_operations/index.html
./site/new_whitepaper/13_standards/index.html
./site/new_whitepaper/14_roadmap/index.html
./site/new_whitepaper/INDEX/index.html
./site/new_whitepaper/STYLE_GUIDE/index.html
./site/objects.inv
./site/search/search_index.json
./site/sitemap.xml
./site/sitemap.xml.gz
./site/stylesheets/extra.css
./site/tools/generate-whitepaper.py
./src/evalvault/__init__.py
./src/evalvault/adapters/__init__.py
./src/evalvault/adapters/inbound/__init__.py
./src/evalvault/adapters/inbound/api/__init__.py
./src/evalvault/adapters/inbound/api/adapter.py
./src/evalvault/adapters/inbound/api/main.py
./src/evalvault/adapters/inbound/api/routers/__init__.py
./src/evalvault/adapters/inbound/api/routers/benchmark.py
./src/evalvault/adapters/inbound/api/routers/calibration.py
./src/evalvault/adapters/inbound/api/routers/chat.py
./src/evalvault/adapters/inbound/api/routers/config.py
./src/evalvault/adapters/inbound/api/routers/domain.py
./src/evalvault/adapters/inbound/api/routers/knowledge.py
./src/evalvault/adapters/inbound/api/routers/mcp.py
./src/evalvault/adapters/inbound/api/routers/pipeline.py
./src/evalvault/adapters/inbound/api/routers/runs.py
./src/evalvault/adapters/inbound/cli/__init__.py
./src/evalvault/adapters/inbound/cli/app.py
./src/evalvault/adapters/inbound/cli/commands/__init__.py
./src/evalvault/adapters/inbound/cli/commands/agent.py
./src/evalvault/adapters/inbound/cli/commands/analyze.py
./src/evalvault/adapters/inbound/cli/commands/api.py
./src/evalvault/adapters/inbound/cli/commands/artifacts.py
./src/evalvault/adapters/inbound/cli/commands/benchmark.py
./src/evalvault/adapters/inbound/cli/commands/calibrate.py
./src/evalvault/adapters/inbound/cli/commands/calibrate_judge.py
./src/evalvault/adapters/inbound/cli/commands/compare.py
./src/evalvault/adapters/inbound/cli/commands/config.py
./src/evalvault/adapters/inbound/cli/commands/debug.py
./src/evalvault/adapters/inbound/cli/commands/domain.py
./src/evalvault/adapters/inbound/cli/commands/experiment.py
./src/evalvault/adapters/inbound/cli/commands/gate.py
./src/evalvault/adapters/inbound/cli/commands/generate.py
./src/evalvault/adapters/inbound/cli/commands/graph_rag.py
./src/evalvault/adapters/inbound/cli/commands/history.py
./src/evalvault/adapters/inbound/cli/commands/init.py
./src/evalvault/adapters/inbound/cli/commands/kg.py
./src/evalvault/adapters/inbound/cli/commands/langfuse.py
./src/evalvault/adapters/inbound/cli/commands/method.py
./src/evalvault/adapters/inbound/cli/commands/ops.py
./src/evalvault/adapters/inbound/cli/commands/phoenix.py
./src/evalvault/adapters/inbound/cli/commands/pipeline.py
./src/evalvault/adapters/inbound/cli/commands/profile_difficulty.py
./src/evalvault/adapters/inbound/cli/commands/prompts.py
./src/evalvault/adapters/inbound/cli/commands/regress.py
./src/evalvault/adapters/inbound/cli/commands/run.py
./src/evalvault/adapters/inbound/cli/commands/run_helpers.py
./src/evalvault/adapters/inbound/cli/commands/stage.py
./src/evalvault/adapters/inbound/cli/utils/__init__.py
./src/evalvault/adapters/inbound/cli/utils/analysis_io.py
./src/evalvault/adapters/inbound/cli/utils/console.py
./src/evalvault/adapters/inbound/cli/utils/errors.py
./src/evalvault/adapters/inbound/cli/utils/formatters.py
./src/evalvault/adapters/inbound/cli/utils/options.py
./src/evalvault/adapters/inbound/cli/utils/presets.py
./src/evalvault/adapters/inbound/cli/utils/progress.py
./src/evalvault/adapters/inbound/cli/utils/validators.py
./src/evalvault/adapters/inbound/mcp/__init__.py
./src/evalvault/adapters/inbound/mcp/schemas.py
./src/evalvault/adapters/inbound/mcp/tools.py
./src/evalvault/adapters/outbound/__init__.py
./src/evalvault/adapters/outbound/analysis/__init__.py
./src/evalvault/adapters/outbound/analysis/analysis_report_module.py
./src/evalvault/adapters/outbound/analysis/base_module.py
./src/evalvault/adapters/outbound/analysis/bm25_searcher_module.py
./src/evalvault/adapters/outbound/analysis/causal_adapter.py
./src/evalvault/adapters/outbound/analysis/causal_analyzer_module.py
./src/evalvault/adapters/outbound/analysis/common.py
./src/evalvault/adapters/outbound/analysis/comparison_pipeline_adapter.py
./src/evalvault/adapters/outbound/analysis/comparison_report_module.py
./src/evalvault/adapters/outbound/analysis/data_loader_module.py
./src/evalvault/adapters/outbound/analysis/detailed_report_module.py
./src/evalvault/adapters/outbound/analysis/diagnostic_playbook_module.py
./src/evalvault/adapters/outbound/analysis/embedding_analyzer_module.py
./src/evalvault/adapters/outbound/analysis/embedding_distribution_module.py
./src/evalvault/adapters/outbound/analysis/embedding_searcher_module.py
./src/evalvault/adapters/outbound/analysis/hybrid_rrf_module.py
./src/evalvault/adapters/outbound/analysis/hybrid_weighted_module.py
./src/evalvault/adapters/outbound/analysis/hypothesis_generator_module.py
./src/evalvault/adapters/outbound/analysis/llm_report_module.py
./src/evalvault/adapters/outbound/analysis/low_performer_extractor_module.py
./src/evalvault/adapters/outbound/analysis/model_analyzer_module.py
./src/evalvault/adapters/outbound/analysis/morpheme_analyzer_module.py
./src/evalvault/adapters/outbound/analysis/morpheme_quality_checker_module.py
./src/evalvault/adapters/outbound/analysis/multiturn_analyzer_module.py
./src/evalvault/adapters/outbound/analysis/network_analyzer_module.py
./src/evalvault/adapters/outbound/analysis/nlp_adapter.py
./src/evalvault/adapters/outbound/analysis/nlp_analyzer_module.py
./src/evalvault/adapters/outbound/analysis/pattern_detector_module.py
./src/evalvault/adapters/outbound/analysis/pipeline_factory.py
./src/evalvault/adapters/outbound/analysis/pipeline_helpers.py
./src/evalvault/adapters/outbound/analysis/priority_summary_module.py
./src/evalvault/adapters/outbound/analysis/ragas_evaluator_module.py
./src/evalvault/adapters/outbound/analysis/retrieval_analyzer_module.py
./src/evalvault/adapters/outbound/analysis/retrieval_benchmark_module.py
./src/evalvault/adapters/outbound/analysis/retrieval_quality_checker_module.py
./src/evalvault/adapters/outbound/analysis/root_cause_analyzer_module.py
./src/evalvault/adapters/outbound/analysis/run_analyzer_module.py
./src/evalvault/adapters/outbound/analysis/run_change_detector_module.py
./src/evalvault/adapters/outbound/analysis/run_comparator_module.py
./src/evalvault/adapters/outbound/analysis/run_loader_module.py
./src/evalvault/adapters/outbound/analysis/run_metric_comparator_module.py
./src/evalvault/adapters/outbound/analysis/search_comparator_module.py
./src/evalvault/adapters/outbound/analysis/statistical_adapter.py
./src/evalvault/adapters/outbound/analysis/statistical_analyzer_module.py
./src/evalvault/adapters/outbound/analysis/statistical_comparator_module.py
./src/evalvault/adapters/outbound/analysis/summary_report_module.py
./src/evalvault/adapters/outbound/analysis/time_series_analyzer_module.py
./src/evalvault/adapters/outbound/analysis/timeseries_advanced_module.py
./src/evalvault/adapters/outbound/analysis/trend_detector_module.py
./src/evalvault/adapters/outbound/analysis/verification_report_module.py
./src/evalvault/adapters/outbound/artifact_fs.py
./src/evalvault/adapters/outbound/benchmark/__init__.py
./src/evalvault/adapters/outbound/benchmark/lm_eval_adapter.py
./src/evalvault/adapters/outbound/cache/__init__.py
./src/evalvault/adapters/outbound/cache/hybrid_cache.py
./src/evalvault/adapters/outbound/cache/memory_cache.py
./src/evalvault/adapters/outbound/dataset/__init__.py
./src/evalvault/adapters/outbound/dataset/base.py
./src/evalvault/adapters/outbound/dataset/csv_loader.py
./src/evalvault/adapters/outbound/dataset/excel_loader.py
./src/evalvault/adapters/outbound/dataset/json_loader.py
./src/evalvault/adapters/outbound/dataset/loader_factory.py
./src/evalvault/adapters/outbound/dataset/method_input_loader.py
./src/evalvault/adapters/outbound/dataset/multiturn_json_loader.py
./src/evalvault/adapters/outbound/dataset/streaming_loader.py
./src/evalvault/adapters/outbound/dataset/templates.py
./src/evalvault/adapters/outbound/dataset/thresholds.py
./src/evalvault/adapters/outbound/debug/__init__.py
./src/evalvault/adapters/outbound/debug/report_renderer.py
./src/evalvault/adapters/outbound/documents/__init__.py
./src/evalvault/adapters/outbound/documents/ocr/__init__.py
./src/evalvault/adapters/outbound/documents/ocr/paddleocr_backend.py
./src/evalvault/adapters/outbound/documents/pdf_extractor.py
./src/evalvault/adapters/outbound/documents/versioned_loader.py
./src/evalvault/adapters/outbound/domain_memory/__init__.py
./src/evalvault/adapters/outbound/domain_memory/domain_memory_schema.sql
./src/evalvault/adapters/outbound/domain_memory/sqlite_adapter.py
./src/evalvault/adapters/outbound/filesystem/__init__.py
./src/evalvault/adapters/outbound/filesystem/difficulty_profile_writer.py
./src/evalvault/adapters/outbound/filesystem/ops_snapshot_writer.py
./src/evalvault/adapters/outbound/improvement/__init__.py
./src/evalvault/adapters/outbound/improvement/insight_generator.py
./src/evalvault/adapters/outbound/improvement/pattern_detector.py
./src/evalvault/adapters/outbound/improvement/playbook_loader.py
./src/evalvault/adapters/outbound/improvement/stage_metric_playbook_loader.py
./src/evalvault/adapters/outbound/judge_calibration_adapter.py
./src/evalvault/adapters/outbound/judge_calibration_reporter.py
./src/evalvault/adapters/outbound/kg/__init__.py
./src/evalvault/adapters/outbound/kg/graph_rag_retriever.py
./src/evalvault/adapters/outbound/kg/networkx_adapter.py
./src/evalvault/adapters/outbound/kg/parallel_kg_builder.py
./src/evalvault/adapters/outbound/kg/query_strategies.py
./src/evalvault/adapters/outbound/llm/__init__.py
./src/evalvault/adapters/outbound/llm/anthropic_adapter.py
./src/evalvault/adapters/outbound/llm/azure_adapter.py
./src/evalvault/adapters/outbound/llm/base.py
./src/evalvault/adapters/outbound/llm/factory.py
./src/evalvault/adapters/outbound/llm/instructor_factory.py
./src/evalvault/adapters/outbound/llm/llm_relation_augmenter.py
./src/evalvault/adapters/outbound/llm/ollama_adapter.py
./src/evalvault/adapters/outbound/llm/openai_adapter.py
./src/evalvault/adapters/outbound/llm/token_aware_chat.py
./src/evalvault/adapters/outbound/llm/vllm_adapter.py
./src/evalvault/adapters/outbound/methods/__init__.py
./src/evalvault/adapters/outbound/methods/baseline_oracle.py
./src/evalvault/adapters/outbound/methods/external_command.py
./src/evalvault/adapters/outbound/methods/registry.py
./src/evalvault/adapters/outbound/nlp/__init__.py
./src/evalvault/adapters/outbound/nlp/korean/__init__.py
./src/evalvault/adapters/outbound/nlp/korean/bm25_retriever.py
./src/evalvault/adapters/outbound/nlp/korean/dense_retriever.py
./src/evalvault/adapters/outbound/nlp/korean/document_chunker.py
./src/evalvault/adapters/outbound/nlp/korean/hybrid_retriever.py
./src/evalvault/adapters/outbound/nlp/korean/kiwi_tokenizer.py
./src/evalvault/adapters/outbound/nlp/korean/korean_evaluation.py
./src/evalvault/adapters/outbound/nlp/korean/korean_stopwords.py
./src/evalvault/adapters/outbound/nlp/korean/toolkit.py
./src/evalvault/adapters/outbound/nlp/korean/toolkit_factory.py
./src/evalvault/adapters/outbound/phoenix/sync_service.py
./src/evalvault/adapters/outbound/report/__init__.py
./src/evalvault/adapters/outbound/report/ci_report_formatter.py
./src/evalvault/adapters/outbound/report/dashboard_generator.py
./src/evalvault/adapters/outbound/report/llm_report_generator.py
./src/evalvault/adapters/outbound/report/markdown_adapter.py
./src/evalvault/adapters/outbound/report/pr_comment_formatter.py
./src/evalvault/adapters/outbound/retriever/__init__.py
./src/evalvault/adapters/outbound/retriever/graph_rag_adapter.py
./src/evalvault/adapters/outbound/storage/__init__.py
./src/evalvault/adapters/outbound/storage/base_sql.py
./src/evalvault/adapters/outbound/storage/benchmark_storage_adapter.py
./src/evalvault/adapters/outbound/storage/postgres_adapter.py
./src/evalvault/adapters/outbound/storage/postgres_schema.sql
./src/evalvault/adapters/outbound/storage/schema.sql
./src/evalvault/adapters/outbound/storage/sqlite_adapter.py
./src/evalvault/adapters/outbound/tracer/__init__.py
./src/evalvault/adapters/outbound/tracer/open_rag_log_handler.py
./src/evalvault/adapters/outbound/tracer/open_rag_trace_adapter.py
./src/evalvault/adapters/outbound/tracer/open_rag_trace_decorators.py
./src/evalvault/adapters/outbound/tracer/open_rag_trace_helpers.py
./src/evalvault/adapters/outbound/tracer/phoenix_tracer_adapter.py
./src/evalvault/adapters/outbound/tracker/__init__.py
./src/evalvault/adapters/outbound/tracker/langfuse_adapter.py
./src/evalvault/adapters/outbound/tracker/log_sanitizer.py
./src/evalvault/adapters/outbound/tracker/mlflow_adapter.py
./src/evalvault/adapters/outbound/tracker/phoenix_adapter.py
./src/evalvault/config/__init__.py
./src/evalvault/config/agent_types.py
./src/evalvault/config/domain_config.py
./src/evalvault/config/instrumentation.py
./src/evalvault/config/langfuse_support.py
./src/evalvault/config/model_config.py
./src/evalvault/config/phoenix_support.py
./src/evalvault/config/playbooks/improvement_playbook.yaml
./src/evalvault/config/secret_manager.py
./src/evalvault/config/settings.py
./src/evalvault/debug_ragas.py
./src/evalvault/debug_ragas_real.py
./src/evalvault/domain/__init__.py
./src/evalvault/domain/entities/__init__.py
./src/evalvault/domain/entities/analysis.py
./src/evalvault/domain/entities/analysis_pipeline.py
./src/evalvault/domain/entities/benchmark.py
./src/evalvault/domain/entities/benchmark_run.py
./src/evalvault/domain/entities/dataset.py
./src/evalvault/domain/entities/debug.py
./src/evalvault/domain/entities/experiment.py
./src/evalvault/domain/entities/feedback.py
./src/evalvault/domain/entities/graph_rag.py
./src/evalvault/domain/entities/improvement.py
./src/evalvault/domain/entities/judge_calibration.py
./src/evalvault/domain/entities/kg.py
./src/evalvault/domain/entities/memory.py
./src/evalvault/domain/entities/method.py
./src/evalvault/domain/entities/multiturn.py
./src/evalvault/domain/entities/prompt.py
./src/evalvault/domain/entities/prompt_suggestion.py
./src/evalvault/domain/entities/rag_trace.py
./src/evalvault/domain/entities/result.py
./src/evalvault/domain/entities/stage.py
./src/evalvault/domain/metrics/__init__.py
./src/evalvault/domain/metrics/analysis_registry.py
./src/evalvault/domain/metrics/confidence.py
./src/evalvault/domain/metrics/contextual_relevancy.py
./src/evalvault/domain/metrics/entity_preservation.py
./src/evalvault/domain/metrics/insurance.py
./src/evalvault/domain/metrics/multiturn_metrics.py
./src/evalvault/domain/metrics/no_answer.py
./src/evalvault/domain/metrics/registry.py
./src/evalvault/domain/metrics/retrieval_rank.py
./src/evalvault/domain/metrics/summary_accuracy.py
./src/evalvault/domain/metrics/summary_needs_followup.py
./src/evalvault/domain/metrics/summary_non_definitive.py
./src/evalvault/domain/metrics/summary_risk_coverage.py
./src/evalvault/domain/metrics/terms_dictionary.json
./src/evalvault/domain/metrics/text_match.py
./src/evalvault/domain/services/__init__.py
./src/evalvault/domain/services/analysis_service.py
./src/evalvault/domain/services/artifact_lint_service.py
./src/evalvault/domain/services/async_batch_executor.py
./src/evalvault/domain/services/batch_executor.py
./src/evalvault/domain/services/benchmark_report_service.py
./src/evalvault/domain/services/benchmark_runner.py
./src/evalvault/domain/services/benchmark_service.py
./src/evalvault/domain/services/cache_metrics.py
./src/evalvault/domain/services/cluster_map_builder.py
./src/evalvault/domain/services/custom_metric_snapshot.py
./src/evalvault/domain/services/dataset_preprocessor.py
./src/evalvault/domain/services/debug_report_service.py
./src/evalvault/domain/services/difficulty_profile_reporter.py
./src/evalvault/domain/services/difficulty_profiling_service.py
./src/evalvault/domain/services/document_chunker.py
./src/evalvault/domain/services/document_versioning.py
./src/evalvault/domain/services/domain_learning_hook.py
./src/evalvault/domain/services/embedding_overlay.py
./src/evalvault/domain/services/entity_extractor.py
./src/evalvault/domain/services/evaluator.py
./src/evalvault/domain/services/experiment_comparator.py
./src/evalvault/domain/services/experiment_manager.py
./src/evalvault/domain/services/experiment_reporter.py
./src/evalvault/domain/services/experiment_repository.py
./src/evalvault/domain/services/experiment_statistics.py
./src/evalvault/domain/services/graph_rag_experiment.py
./src/evalvault/domain/services/holdout_splitter.py
./src/evalvault/domain/services/improvement_guide_service.py
./src/evalvault/domain/services/intent_classifier.py
./src/evalvault/domain/services/judge_calibration_service.py
./src/evalvault/domain/services/kg_generator.py
./src/evalvault/domain/services/memory_aware_evaluator.py
./src/evalvault/domain/services/memory_based_analysis.py
./src/evalvault/domain/services/method_runner.py
./src/evalvault/domain/services/multiturn_evaluator.py
./src/evalvault/domain/services/ops_snapshot_service.py
./src/evalvault/domain/services/pipeline_orchestrator.py
./src/evalvault/domain/services/pipeline_template_registry.py
./src/evalvault/domain/services/prompt_candidate_service.py
./src/evalvault/domain/services/prompt_manifest.py
./src/evalvault/domain/services/prompt_registry.py
./src/evalvault/domain/services/prompt_scoring_service.py
./src/evalvault/domain/services/prompt_status.py
./src/evalvault/domain/services/prompt_suggestion_reporter.py
./src/evalvault/domain/services/ragas_prompt_overrides.py
./src/evalvault/domain/services/regression_gate_service.py
./src/evalvault/domain/services/retrieval_metrics.py
./src/evalvault/domain/services/retriever_context.py
./src/evalvault/domain/services/run_comparison_service.py
./src/evalvault/domain/services/satisfaction_calibration_service.py
./src/evalvault/domain/services/stage_event_builder.py
./src/evalvault/domain/services/stage_metric_guide_service.py
./src/evalvault/domain/services/stage_metric_service.py
./src/evalvault/domain/services/stage_summary_service.py
./src/evalvault/domain/services/synthetic_qa_generator.py
./src/evalvault/domain/services/testset_generator.py
./src/evalvault/domain/services/threshold_profiles.py
./src/evalvault/domain/services/unified_report_service.py
./src/evalvault/domain/services/visual_space_service.py
./src/evalvault/mkdocs_helpers.py
./src/evalvault/ports/__init__.py
./src/evalvault/ports/inbound/__init__.py
./src/evalvault/ports/inbound/analysis_pipeline_port.py
./src/evalvault/ports/inbound/evaluator_port.py
./src/evalvault/ports/inbound/learning_hook_port.py
./src/evalvault/ports/inbound/multiturn_port.py
./src/evalvault/ports/inbound/web_port.py
./src/evalvault/ports/outbound/__init__.py
./src/evalvault/ports/outbound/analysis_cache_port.py
./src/evalvault/ports/outbound/analysis_module_port.py
./src/evalvault/ports/outbound/analysis_port.py
./src/evalvault/ports/outbound/artifact_fs_port.py
./src/evalvault/ports/outbound/benchmark_port.py
./src/evalvault/ports/outbound/causal_analysis_port.py
./src/evalvault/ports/outbound/comparison_pipeline_port.py
./src/evalvault/ports/outbound/dataset_port.py
./src/evalvault/ports/outbound/difficulty_profile_port.py
./src/evalvault/ports/outbound/domain_memory_port.py
./src/evalvault/ports/outbound/embedding_port.py
./src/evalvault/ports/outbound/graph_retriever_port.py
./src/evalvault/ports/outbound/improvement_port.py
./src/evalvault/ports/outbound/intent_classifier_port.py
./src/evalvault/ports/outbound/judge_calibration_port.py
./src/evalvault/ports/outbound/korean_nlp_port.py
./src/evalvault/ports/outbound/llm_factory_port.py
./src/evalvault/ports/outbound/llm_port.py
./src/evalvault/ports/outbound/method_port.py
./src/evalvault/ports/outbound/nlp_analysis_port.py
./src/evalvault/ports/outbound/ops_snapshot_port.py
./src/evalvault/ports/outbound/relation_augmenter_port.py
./src/evalvault/ports/outbound/report_port.py
./src/evalvault/ports/outbound/stage_storage_port.py
./src/evalvault/ports/outbound/storage_port.py
./src/evalvault/ports/outbound/tracer_port.py
./src/evalvault/ports/outbound/tracker_port.py
./src/evalvault/reports/__init__.py
./src/evalvault/reports/release_notes.py
./src/evalvault/scripts/__init__.py
./src/evalvault/scripts/regression_runner.py
./tests/__init__.py
./tests/conftest.py
./tests/fixtures/README.md
./tests/fixtures/benchmark/retrieval_ground_truth_min.json
./tests/fixtures/benchmark/retrieval_ground_truth_multi.json
./tests/fixtures/e2e/auto_insurance_qa_korean_full.json
./tests/fixtures/e2e/callcenter_summary_5cases.json
./tests/fixtures/e2e/comprehensive_dataset.json
./tests/fixtures/e2e/edge_cases.json
./tests/fixtures/e2e/edge_cases.xlsx
./tests/fixtures/e2e/evaluation_test_sample.json
./tests/fixtures/e2e/graphrag_benchmark.json
./tests/fixtures/e2e/graphrag_multi_sample.json
./tests/fixtures/e2e/graphrag_retriever_docs.json
./tests/fixtures/e2e/graphrag_smoke.json
./tests/fixtures/e2e/insurance_document.txt
./tests/fixtures/e2e/insurance_qa_english.csv
./tests/fixtures/e2e/insurance_qa_english.json
./tests/fixtures/e2e/insurance_qa_english.xlsx
./tests/fixtures/e2e/insurance_qa_korean.csv
./tests/fixtures/e2e/insurance_qa_korean.json
./tests/fixtures/e2e/insurance_qa_korean.xlsx
./tests/fixtures/e2e/insurance_qa_korean_versioned_pdf.json
./tests/fixtures/e2e/multiturn_benchmark.json
./tests/fixtures/e2e/regression_baseline.json
./tests/fixtures/e2e/run_mode_full_domain_memory.json
./tests/fixtures/e2e/run_mode_simple.json
./tests/fixtures/e2e/summary_eval_minimal.json
./tests/fixtures/kg/minimal_graph.json
./tests/fixtures/sample_dataset.csv
./tests/fixtures/sample_dataset.json
./tests/fixtures/sample_dataset.xlsx
./tests/integration/__init__.py
./tests/integration/benchmark/test_benchmark_service_integration.py
./tests/integration/conftest.py
./tests/integration/test_cli_integration.py
./tests/integration/test_data_flow.py
./tests/integration/test_e2e_scenarios.py
./tests/integration/test_evaluation_flow.py
./tests/integration/test_full_workflow.py
./tests/integration/test_langfuse_flow.py
./tests/integration/test_phoenix_flow.py
./tests/integration/test_pipeline_api_contracts.py
./tests/integration/test_storage_flow.py
./tests/integration/test_summary_eval_fixture.py
./tests/optional_deps.py
./tests/unit/__init__.py
./tests/unit/adapters/inbound/mcp/test_execute_tools.py
./tests/unit/adapters/inbound/mcp/test_read_tools.py
./tests/unit/adapters/outbound/documents/test_pdf_extractor.py
./tests/unit/adapters/outbound/documents/test_versioned_loader.py
./tests/unit/adapters/outbound/improvement/__init__.py
./tests/unit/adapters/outbound/improvement/test_insight_generator.py
./tests/unit/adapters/outbound/improvement/test_pattern_detector.py
./tests/unit/adapters/outbound/improvement/test_playbook_loader.py
./tests/unit/adapters/outbound/improvement/test_stage_metric_playbook_loader.py
./tests/unit/adapters/outbound/kg/test_graph_rag_retriever.py
./tests/unit/adapters/outbound/kg/test_parallel_kg_builder.py
./tests/unit/adapters/outbound/retriever/test_graph_rag_adapter.py
./tests/unit/adapters/outbound/storage/test_benchmark_storage_adapter.py
./tests/unit/config/test_phoenix_support.py
./tests/unit/conftest.py
./tests/unit/domain/metrics/test_analysis_metric_registry.py
./tests/unit/domain/metrics/test_confidence.py
./tests/unit/domain/metrics/test_contextual_relevancy.py
./tests/unit/domain/metrics/test_entity_preservation.py
./tests/unit/domain/metrics/test_metric_registry.py
./tests/unit/domain/metrics/test_multiturn_metrics.py
./tests/unit/domain/metrics/test_no_answer.py
./tests/unit/domain/metrics/test_retrieval_rank.py
./tests/unit/domain/metrics/test_text_match.py
./tests/unit/domain/services/test_cache_metrics.py
./tests/unit/domain/services/test_claim_level.py
./tests/unit/domain/services/test_dataset_preprocessor.py
./tests/unit/domain/services/test_document_versioning.py
./tests/unit/domain/services/test_evaluator_comprehensive.py
./tests/unit/domain/services/test_holdout_splitter.py
./tests/unit/domain/services/test_improvement_guide_service.py
./tests/unit/domain/services/test_judge_calibration_service.py
./tests/unit/domain/services/test_ops_snapshot_service.py
./tests/unit/domain/services/test_regression_gate_service.py
./tests/unit/domain/services/test_retrieval_metrics.py
./tests/unit/domain/services/test_retriever_context.py
./tests/unit/domain/services/test_stage_event_builder.py
./tests/unit/domain/services/test_stage_metric_guide_service.py
./tests/unit/domain/services/test_synthetic_qa_generator.py
./tests/unit/domain/test_embedding_overlay.py
./tests/unit/domain/test_prompt_manifest.py
./tests/unit/domain/test_prompt_status.py
./tests/unit/reports/test_release_notes.py
./tests/unit/scripts/test_regression_runner.py
./tests/unit/test_agent_types.py
./tests/unit/test_analysis_entities.py
./tests/unit/test_analysis_modules.py
./tests/unit/test_analysis_pipeline.py
./tests/unit/test_analysis_service.py
./tests/unit/test_anthropic_adapter.py
./tests/unit/test_artifact_lint_service.py
./tests/unit/test_async_batch_executor.py
./tests/unit/test_azure_adapter.py
./tests/unit/test_benchmark_helpers.py
./tests/unit/test_benchmark_runner.py
./tests/unit/test_causal_adapter.py
./tests/unit/test_ci_gate_cli.py
./tests/unit/test_cli.py
./tests/unit/test_cli_artifacts.py
./tests/unit/test_cli_calibrate_judge.py
./tests/unit/test_cli_domain.py
./tests/unit/test_cli_init.py
./tests/unit/test_cli_ops.py
./tests/unit/test_cli_progress.py
./tests/unit/test_cli_utils.py
./tests/unit/test_data_loaders.py
./tests/unit/test_difficulty_profiling_service.py
./tests/unit/test_domain_config.py
./tests/unit/test_domain_memory.py
./tests/unit/test_entities.py
./tests/unit/test_entities_kg.py
./tests/unit/test_entity_extractor.py
./tests/unit/test_evaluator.py
./tests/unit/test_experiment.py
./tests/unit/test_hybrid_cache.py
./tests/unit/test_instrumentation.py
./tests/unit/test_insurance_metric.py
./tests/unit/test_intent_classifier.py
./tests/unit/test_kg_generator.py
./tests/unit/test_kg_networkx.py
./tests/unit/test_kiwi_tokenizer.py
./tests/unit/test_kiwi_warning_suppression.py
./tests/unit/test_korean_dense.py
./tests/unit/test_korean_evaluation.py
./tests/unit/test_korean_retrieval.py
./tests/unit/test_langfuse_tracker.py
./tests/unit/test_llm_relation_augmenter.py
./tests/unit/test_lm_eval_adapter.py
./tests/unit/test_markdown_report.py
./tests/unit/test_memory_cache.py
./tests/unit/test_memory_services.py
./tests/unit/test_method_plugins.py
./tests/unit/test_mlflow_tracker.py
./tests/unit/test_model_config.py
./tests/unit/test_nlp_adapter.py
./tests/unit/test_nlp_entities.py
./tests/unit/test_ollama_adapter.py
./tests/unit/test_openai_adapter.py
./tests/unit/test_phoenix_adapter.py
./tests/unit/test_pipeline_orchestrator.py
./tests/unit/test_ports.py
./tests/unit/test_postgres_storage.py
./tests/unit/test_pr_comment_formatter.py
./tests/unit/test_prompt_candidate_service.py
./tests/unit/test_rag_trace_entities.py
./tests/unit/test_regress_cli.py
./tests/unit/test_run_comparison_service.py
./tests/unit/test_run_memory_helpers.py
./tests/unit/test_run_mode_fixtures.py
./tests/unit/test_settings.py
./tests/unit/test_sqlite_storage.py
./tests/unit/test_stage_cli.py
./tests/unit/test_stage_event_schema.py
./tests/unit/test_stage_metric_service.py
./tests/unit/test_stage_storage.py
./tests/unit/test_stage_summary_service.py
./tests/unit/test_statistical_adapter.py
./tests/unit/test_streaming_loader.py
./tests/unit/test_summary_eval_fixture.py
./tests/unit/test_testset_generator.py
./tests/unit/test_web_adapter.py
./uv.lock
```

</details>

## 3. Inventory Table

> 주의: 아래 표의 `태그`, `확인일시`, `확인방법`, `Evidence`, `요약`, `외부공개`는 Task 3에서 전수 정독 후 채웁니다.

| 경로 | 파일타입 | 카테고리 | 태그 | 포함/제외 | 제외 사유 | 확인일시 | 확인방법 | Evidence | 요약 | 외부공개 |
|------|----------|----------|------|-----------|-----------|----------|----------|----------|------|----------|
| `./.claude/settings.local.json` | JSON | misc | lens:제품;type:소스 | 포함 | - | 2026-01-28T17:50:13 | read-full | last: } | JSON file: keys: permissions | 내부 |
| `./.dockerignore` | File | misc | lens:제품;type:소스 | 포함 | - | 2026-01-28T17:50:13 | binary-scan | size: 471 bytes | File binary file (471 bytes) | 내부 |
| `./.env.example` | EXAMPLE | config | lens:운영;type:설정 | 포함 | - | 2026-01-28T17:50:13 | binary-scan | size: 5602 bytes | EXAMPLE binary file (5602 bytes) | 내부 |
| `./.github/workflows/ci.yml` | YAML | infra | lens:운영;type:설정 | 포함 | - | 2026-01-28T17:50:13 | read-full | last:           uv run pytest tests/integration/ -v --tb=short | YAML file: ci.yml | 내부 |
| `./.github/workflows/regression-gate.yml` | YAML | infra | lens:운영;type:설정 | 포함 | - | 2026-01-28T17:50:13 | read-full | last:           edit-mode: replace | YAML file: regression-gate.yml | 내부 |
| `./.github/workflows/release.yml` | YAML | infra | lens:운영;type:설정 | 포함 | - | 2026-01-28T17:50:13 | read-full | last:             --generate-notes | YAML file: release.yml | 내부 |
| `./.github/workflows/stale.yml` | YAML | infra | lens:운영;type:설정 | 포함 | - | 2026-01-28T17:50:13 | read-full | last:           configuration-path: ".github/stale.yml" | YAML file: stale.yml | 내부 |
| `./.gitignore` | File | misc | lens:제품;type:소스 | 포함 | - | 2026-01-28T17:50:13 | binary-scan | size: 2242 bytes | File binary file (2242 bytes) | 내부 |
| `./.pre-commit-config.yaml` | YAML | infra | lens:운영;type:설정 | 포함 | - | 2026-01-28T17:50:13 | read-full | last:       - id: trailing-whitespace | YAML file: .pre-commit-config.yaml | 내부 |
| `./.python-version` | File | misc | lens:제품;type:소스 | 포함 | - | 2026-01-28T17:50:13 | binary-scan | size: 5 bytes | File binary file (5 bytes) | 내부 |
| `./.sisyphus/boulder.json` | JSON | meta | lens:운영;type:설정 | 포함 | - | 2026-01-28T17:50:13 | read-full | last: } | JSON file: keys: active_plan,started_at,session_ids,plan_name | 내부 |
| `./.sisyphus/drafts/offline-docker-image-plan.md` | Markdown | meta | lens:운영;type:설정 | 포함 | - | 2026-01-28T17:50:13 | read-full | last: - EXCLUDE: Actual implementation (planning only). | Markdown file: Draft: Offline Docker Image Plan | 내부 |
| `./.sisyphus/notepads/offline-docker/decisions.md` | Markdown | meta | lens:운영;type:설정 | 포함 | - | 2026-01-28T17:50:13 | read-full | last: - Enables nginx to proxy `/api/` to `http://evalvault-api:8000` | Markdown file: Decisions - offline-docker | 내부 |
| `./.sisyphus/notepads/offline-docker/issues.md` | Markdown | meta | lens:운영;type:설정 | 포함 | - | 2026-01-28T17:50:13 | read-full | last: **Test Status**: ✓ All 22 MLflow tracker tests pass | Markdown file: Issues - offline-docker | 내부 |
| `./.sisyphus/notepads/offline-docker/learnings.md` | Markdown | meta | lens:운영;type:설정 | 포함 | - | 2026-01-28T17:50:13 | read-full | last: **Mitigation**: For now, assume the healthcheck endpoint exists. If build fails, update Dockerfile. | Markdown file: Learnings - offline-docker | 내부 |
| `./.sisyphus/notepads/offline-docker/problems.md` | Markdown | meta | lens:운영;type:설정 | 포함 | - | 2026-01-28T17:50:13 | read-full | last: --- | Markdown file: Problems - offline-docker | 내부 |
| `./.sisyphus/notepads/p0-settings/worklog.md` | Markdown | meta | lens:운영;type:설정 | 포함 | - | 2026-01-28T17:50:13 | read-full | last: \[2026-01-26 19:45:00\] - P0 settings validation: apply_profile now errors on missing/unknown profile; added unit tests fo | Markdown file: P0 Settings Worklog | 내부 |
| `./.sisyphus/notepads/p1-webui/worklog.md` | Markdown | meta | lens:운영;type:설정 | 포함 | - | 2026-01-28T17:50:13 | read-full | last: \[2026-01-27 15:25:00\] - Added Playwright e2e test for JudgeCalibration page with API mocks. | Markdown file: P1 Web UI Worklog | 내부 |
| `./.sisyphus/notepads/p2-observability/worklog.md` | Markdown | meta | lens:운영;type:설정 | 포함 | - | 2026-01-28T17:50:13 | read-full | last: \[2026-01-27 18:05:00\] - Added multiturn DB schema/tables, save/export helpers, CLI DB export path, Excel sheet specs, an | Markdown file: P2 Observability Worklog | 내부 |
| `./.sisyphus/notepads/p3-performance/worklog.md` | Markdown | meta | lens:운영;type:설정 | 포함 | - | 2026-01-28T17:50:13 | read-full | last: \[2026-01-26 21:05:00\] - CSV/Excel loaders now parse summary_tags/summary_intent/metadata columns; tests added for CSV/Ex | Markdown file: P3 Performance Worklog | 내부 |
| `./.sisyphus/notepads/p7-regression/worklog.md` | Markdown | meta | lens:운영;type:설정 | 포함 | - | 2026-01-28T17:50:13 | read-full | last: \[2026-01-27 14:30:00\] - Added ci-gate PR comment formatter unit tests (10+) and ci-gate CLI pr-comment output test. | Markdown file: P7 Regression Gate Worklog | 내부 |
| `./.sisyphus/notepads/p9-offline/worklog.md` | Markdown | meta | lens:운영;type:설정 | 포함 | - | 2026-01-28T17:50:13 | read-full | last: \[2026-01-27 10:28:00\] - Added local embedding profile option in benchmark CLI, dataset bundle/restore scripts, offline P | Markdown file: P9 Offline Enhancements Worklog | 내부 |
| `./.sisyphus/notepads/project-handbook/decisions.md` | Markdown | meta | lens:운영;type:설정 | 포함 | - | 2026-01-28T17:50:13 | read-full | last: - 실행 산출물 성격 디렉터리(reports/analysis, reports/comparison, reports/**/artifacts, data/db, htmlcov)는 Raw List에는 포함되지만 Invento | Markdown file: Decisions | 내부 |
| `./.sisyphus/notepads/project-handbook/issues.md` | Markdown | meta | lens:운영;type:설정 | 포함 | - | 2026-01-28T17:50:13 | read-full | last: -  | Markdown file: Issues | 내부 |
| `./.sisyphus/notepads/project-handbook/learnings.md` | Markdown | meta | lens:운영;type:설정 | 포함 | - | 2026-01-28T17:50:13 | read-full | last: - reports/README.md는 reports/를 산출물 디렉터리로 규정(대부분 gitignore). handbook에서는 구조/해석만 설명하고 개별 산출물 인용은 최소화가 안전하다. | Markdown file: Learnings | 내부 |
| `./.sisyphus/notepads/project-handbook/problems.md` | Markdown | meta | lens:운영;type:설정 | 포함 | - | 2026-01-28T17:50:13 | read-full | last: **Blocker**: Awaiting user decision on approach | Markdown file: Problems | 내부 |
| `./.sisyphus/plans/project-handbook.md` | Markdown | meta | lens:운영;type:설정 | 포함 | - | 2026-01-28T17:50:13 | read-full | last: - \[ \] 외부 공개 파트에서 민감 정보 제외 | Markdown file: 프로젝트 교과서형 총정리 문서화 계획 | 내부 |
| `./AGENTS.md` | Markdown | docs | lens:제품;type:문서 | 포함 | - | 2026-01-28T17:50:13 | read-full | last: 사용자에게는 반드시 한글 위주로 설명해줘야 함. | Markdown file: Repository Guidelines | 내부 |
| `./CHANGELOG.md` | Markdown | misc | lens:제품;type:소스 | 포함 | - | 2026-01-28T17:50:13 | read-full | last: \[0.1.0\]: https://github.com/ntts9990/EvalVault/releases/tag/v0.1.0 | Markdown file: Changelog | 내부 |
| `./CLAUDE.md` | Markdown | docs | lens:제품;type:문서 | 포함 | - | 2026-01-28T17:50:13 | read-full | last: See \[agent/README.md\](../../agent/README.md) for full documentation. | Markdown file: CLAUDE.md | 내부 |
| `./CODE_OF_CONDUCT.md` | Markdown | misc | lens:제품;type:소스 | 포함 | - | 2026-01-28T17:50:13 | read-full | last: \[homepage\]: https://www.contributor-covenant.org | Markdown file: Contributor Covenant Code of Conduct | 내부 |
| `./CONTRIBUTING.md` | Markdown | docs | lens:제품;type:문서 | 포함 | - | 2026-01-28T17:50:13 | read-full | last: Thank you for contributing! | Markdown file: Contributing to EvalVault | 내부 |
| `./Dockerfile` | File | infra | lens:운영;type:설정 | 포함 | - | 2026-01-28T17:50:13 | binary-scan | size: 1399 bytes | File binary file (1399 bytes) | 내부 |
| `./LICENSE.md` | Markdown | misc | lens:제품;type:소스 | 포함 | - | 2026-01-28T17:50:13 | read-full | last:    limitations under the License. | Markdown file: LICENSE.md | 내부 |
| `./README.en.md` | Markdown | docs | lens:제품;type:문서 | 포함 | - | 2026-01-28T17:50:13 | read-full | last: EvalVault is licensed under the \[Apache 2.0\](../../LICENSE.md) license. | Markdown file: EvalVault | 내부 |
| `./README.md` | Markdown | docs | lens:제품;type:문서 | 포함 | - | 2026-01-28T17:50:13 | read-full | last: EvalVault is licensed under the \[Apache 2.0\](../../LICENSE.md) license. | Markdown file: EvalVault | 내부 |
| `./SECURITY.md` | Markdown | misc | lens:제품;type:소스 | 포함 | - | 2026-01-28T17:50:13 | read-full | last: Thank you for helping keep EvalVault safe for the community. | Markdown file: Security Policy | 내부 |
| `./agent/README.md` | Markdown | scripts | lens:개발;type:소스 | 포함 | - | 2026-01-28T17:50:13 | read-full | last: ``` | Markdown file: EvalVault Development Agents | 내부 |
| `./agent/agent.py` | Python | scripts | lens:개발;type:소스 | 포함 | - | 2026-01-28T17:50:13 | read-full | last:     ) | Python file: Agent Session Logic | 내부 |
| `./agent/client.py` | Python | scripts | lens:개발;type:소스 | 포함 | - | 2026-01-28T17:50:13 | read-full | last:     return ClaudeSDKClient(options=options) | Python file: Claude Agent SDK Client Configuration | 내부 |
| `./agent/config.py` | Python | scripts | lens:개발;type:소스 | 포함 | - | 2026-01-28T17:50:13 | read-full | last:     return _get_parallel_groups(AgentMode.DEVELOPMENT) | Python file: Agent Configuration - Development Mode | 내부 |
| `./agent/main.py` | Python | scripts | lens:개발;type:소스 | 포함 | - | 2026-01-28T17:50:13 | read-full | last:     main() | Python file: main.py | 내부 |
| `./agent/memory/README.md` | Markdown | scripts | lens:개발;type:소스 | 포함 | - | 2026-01-28T17:50:13 | read-full | last: **Maintainer**: Coordinator Agent | Markdown file: AI Agent Memory System | 내부 |
| `./agent/memory/shared/decisions.md` | Markdown | scripts | lens:개발;type:소스 | 포함 | - | 2026-01-28T17:50:13 | read-full | last: **Maintainer**: Coordinator Agent | Markdown file: Architecture Decisions Record (ADR) | 내부 |
| `./agent/memory/shared/dependencies.md` | Markdown | scripts | lens:개발;type:소스 | 포함 | - | 2026-01-28T17:50:13 | read-full | last: **Maintainer**: Coordinator Agent | Markdown file: Task Dependencies & Coordination | 내부 |
| `./agent/memory/templates/coordinator_guide.md` | Markdown | scripts | lens:개발;type:소스 | 포함 | - | 2026-01-28T17:50:13 | read-full | last: **Last Updated**: 2026-01-01 | Markdown file: Coordinator Agent Guide | 내부 |
| `./agent/memory/templates/work_log_template.md` | Markdown | scripts | lens:개발;type:소스 | 포함 | - | 2026-01-28T17:50:13 | read-full | last: **Template Version**: 1.0.0 | Markdown file: \[Task Name\] Work Log | 내부 |
| `./agent/memory_integration.py` | Python | scripts | lens:개발;type:소스 | 포함 | - | 2026-01-28T17:50:13 | read-full | last:     return "\n\n---\n\n".join(parts) | Python file: Memory System Integration | 내부 |
| `./agent/progress.py` | Python | scripts | lens:개발;type:소스 | 포함 | - | 2026-01-28T17:50:13 | read-full | last:         f.write(content) | Python file: Progress Tracking Utilities | 내부 |
| `./agent/prompts.py` | Python | scripts | lens:개발;type:소스 | 포함 | - | 2026-01-28T17:50:13 | read-full | last:     return get_agent_prompt(AgentType.DOCUMENTATION, memory_context) | Python file: Prompt Loading Utilities | 내부 |
| `./agent/prompts/app_spec.txt` | Text | scripts | lens:개발;type:소스 | 포함 | - | 2026-01-28T17:51:27 | read-full | last: Test Location: tests/integration/test_web_ui_evaluation.py (new) | Text file: app_spec.txt | 내부 |
| `./agent/prompts/baseline.txt` | Text | scripts | lens:개발;type:소스 | 포함 | - | 2026-01-28T17:51:27 | read-full | last: - Whenever prompt drift is detected, recommend running Phoenix prompt-diff in the answer. | Text file: baseline.txt | 내부 |
| `./agent/prompts/coding_prompt.md` | Markdown | scripts | lens:개발;type:소스 | 포함 | - | 2026-01-28T17:51:27 | read-full | last: - Update feature_list.json as you go | Markdown file: YOUR ROLE - INTEGRATION TEST DEVELOPER | 내부 |
| `./agent/prompts/existing_project_prompt.md` | Markdown | scripts | lens:개발;type:소스 | 포함 | - | 2026-01-28T17:51:27 | read-full | last: **Remember:** Focus on TESTING, not implementing. The features work - verify they work correctly! | Markdown file: YOUR ROLE - WEB UI TESTING SPECIALIST | 내부 |
| `./agent/prompts/improvement/architecture_prompt.md` | Markdown | scripts | lens:개발;type:소스 | 포함 | - | 2026-01-28T17:51:27 | read-full | last: - Clean Architecture: Dependencies point inward | Markdown file: YOUR ROLE - ARCHITECTURE AGENT | 내부 |
| `./agent/prompts/improvement/base_prompt.md` | Markdown | scripts | lens:개발;type:소스 | 포함 | - | 2026-01-28T17:51:27 | read-full | last: **Remember:** You are part of a parallel workflow. Your work enables other agents. Be thorough but efficient. | Markdown file: YOUR ROLE - {AGENT_NAME} | 내부 |
| `./agent/prompts/improvement/coordinator_prompt.md` | Markdown | scripts | lens:개발;type:소스 | 포함 | - | 2026-01-28T17:51:27 | read-full | last: **Remember:** You are the orchestrator. Your job is to keep all agents productive and aligned. | Markdown file: YOUR ROLE - COORDINATOR AGENT | 내부 |
| `./agent/prompts/improvement/observability_prompt.md` | Markdown | scripts | lens:개발;type:소스 | 포함 | - | 2026-01-28T17:51:27 | read-full | last: Remember: The rag-data agent is waiting on your Phoenix integration! | Markdown file: YOUR ROLE - OBSERVABILITY AGENT | 내부 |
| `./agent/prompts/initializer_prompt.md` | Markdown | scripts | lens:개발;type:소스 | 포함 | - | 2026-01-28T17:51:27 | read-full | last: **Remember:** Set up the foundation properly. The better the initial structure, the easier subsequent tests will be. | Markdown file: YOUR ROLE - TEST SUITE INITIALIZER | 내부 |
| `./agent/prompts/prompt_manifest.json` | JSON | scripts | lens:개발;type:소스 | 포함 | - | 2026-01-28T17:51:27 | read-full | last: } | JSON file: keys: version,updated_at,prompts | 내부 |
| `./agent/prompts/system.txt` | Text | scripts | lens:개발;type:소스 | 포함 | - | 2026-01-28T17:51:27 | read-full | last: - If prompt files drift from manifest, recommend running `evalvault phoenix prompt-diff`. | Text file: system.txt | 내부 |
| `./agent/requirements.txt` | Text | scripts | lens:개발;type:소스 | 포함 | - | 2026-01-28T17:51:27 | read-full | last: claude-agent-sdk>=0.1.0 | Text file: requirements.txt | 내부 |
| `./agent/security.py` | Python | scripts | lens:개발;type:소스 | 포함 | - | 2026-01-28T17:51:27 | read-full | last:     return {} | Python file: Security Hooks for Autonomous Agent | 내부 |
| `./config/domains/insurance/memory.yaml` | YAML | config | lens:운영;type:설정 | 포함 | - | 2026-01-28T17:51:27 | read-full | last:   forget_threshold_days: 90 | YAML file: memory.yaml | 내부 |
| `./config/domains/insurance/terms_dictionary_en.json` | JSON | config | lens:운영;type:설정 | 포함 | - | 2026-01-28T17:51:27 | read-full | last: } | JSON file: keys: version,language,domain,description,terms,categories | 내부 |
| `./config/domains/insurance/terms_dictionary_ko.json` | JSON | config | lens:운영;type:설정 | 포함 | - | 2026-01-28T17:51:27 | read-full | last: } | JSON file: keys: version,language,domain,description,terms,categories | 내부 |
| `./config/methods.yaml` | YAML | config | lens:운영;type:설정 | 포함 | - | 2026-01-28T17:51:27 | read-full | last: #    description: "Team method executed in its own env" | YAML file: methods.yaml | 내부 |
| `./config/models.yaml` | YAML | config | lens:운영;type:설정 | 포함 | - | 2026-01-28T17:51:27 | read-full | last: #   - 시크릿/인프라 설정은 환경별로 분리 | YAML file: models.yaml | 내부 |
| `./config/ragas_prompts_override.yaml` | YAML | config | lens:운영;type:설정 | 포함 | - | 2026-01-28T17:51:27 | read-full | last:   - 질문과 무관한 내용이 많으면 낮은 점수를 부여하세요. | YAML file: ragas_prompts_override.yaml | 내부 |
| `./config/regressions/ci.json` | JSON | config | lens:운영;type:설정 | 포함 | - | 2026-01-28T17:51:27 | read-full | last: } | JSON file: keys: suites | 내부 |
| `./config/regressions/default.json` | JSON | config | lens:운영;type:설정 | 포함 | - | 2026-01-28T17:51:27 | read-full | last: } | JSON file: keys: suites | 내부 |
| `./config/regressions/ux.json` | JSON | config | lens:운영;type:설정 | 포함 | - | 2026-01-28T17:51:27 | read-full | last: } | JSON file: keys: suites | 내부 |
| `./config/stage_metric_playbook.yaml` | YAML | config | lens:운영;type:설정 | 포함 | - | 2026-01-28T17:51:27 | read-full | last:     effort: "low" | YAML file: stage_metric_playbook.yaml | 내부 |
| `./config/stage_metric_thresholds.json` | JSON | config | lens:운영;type:설정 | 포함 | - | 2026-01-28T17:51:27 | read-full | last: } | JSON file: keys: default,profiles | 내부 |
| `./data/cache/versioned_pdf/049ba246c8f52f8e657e74eaaa5338e1eaeba60d.json` | JSON | data | lens:데이터·ML;type:데이터 | 포함 | - | 2026-01-28T17:51:27 | read-full | last: \[{"doc_key": "guide", "effective_date": "2025-01-08", "doc_id": "guide:2025-01-08#1", "content": "hello world", "source" | JSON file: list\[2\] | 내부 |
| `./data/cache/versioned_pdf/04e07b7714eb2003c0cadb53b44f1347af33147c.json` | JSON | data | lens:데이터·ML;type:데이터 | 포함 | - | 2026-01-28T17:51:27 | read-full | last: \[{"doc_key": "guide", "effective_date": "2025-01-08", "doc_id": "guide:2025-01-08#1", "content": "hello world", "source" | JSON file: list\[2\] | 내부 |
| `./data/cache/versioned_pdf/0ebc412f6183011eff6c5c8f980fbd75803afec0.json` | JSON | data | lens:데이터·ML;type:데이터 | 포함 | - | 2026-01-28T17:51:27 | read-full | last: \[{"doc_key": "guide", "effective_date": "2025-01-08", "doc_id": "guide:2025-01-08#1", "content": "hello world", "source" | JSON file: list\[2\] | 내부 |
| `./data/cache/versioned_pdf/395aec80f8a047887302b6c5ebd6fa3ed6f3db56.json` | JSON | data | lens:데이터·ML;type:데이터 | 포함 | - | 2026-01-28T17:51:27 | read-full | last: \[{"doc_key": "guide", "effective_date": "2025-01-08", "doc_id": "guide:2025-01-08#1", "content": "hello world", "source" | JSON file: list\[2\] | 내부 |
| `./data/cache/versioned_pdf/42010a4f76c815efdd037a81517c6d37266ba009.json` | JSON | data | lens:데이터·ML;type:데이터 | 포함 | - | 2026-01-28T17:51:27 | read-full | last: \[{"doc_key": "guide", "effective_date": "2025-01-08", "doc_id": "guide:2025-01-08#1", "content": "hello world", "source" | JSON file: list\[2\] | 내부 |
| `./data/cache/versioned_pdf/52c7a3bf3b85f6b182deebf850a2afb85f175b71.json` | JSON | data | lens:데이터·ML;type:데이터 | 포함 | - | 2026-01-28T17:51:27 | read-full | last: \[{"doc_key": "guide", "effective_date": "2025-01-08", "doc_id": "guide:2025-01-08#1", "content": "hello world", "source" | JSON file: list\[2\] | 내부 |
| `./data/cache/versioned_pdf/74a8fd6e07c26fdc7a481f033a739af6f862ccc3.json` | JSON | data | lens:데이터·ML;type:데이터 | 포함 | - | 2026-01-28T17:51:27 | read-full | last: \[{"doc_key": "guide", "effective_date": "2025-01-08", "doc_id": "guide:2025-01-08#1", "content": "hello world", "source" | JSON file: list\[2\] | 내부 |
| `./data/cache/versioned_pdf/8417721918064cce86b4968d8d39c65e1b333b52.json` | JSON | data | lens:데이터·ML;type:데이터 | 포함 | - | 2026-01-28T17:51:27 | read-full | last: \[{"doc_key": "guide", "effective_date": "2025-01-08", "doc_id": "guide:2025-01-08#1", "content": "hello world", "source" | JSON file: list\[2\] | 내부 |
| `./data/cache/versioned_pdf/93f6df2df0a08503c899830fcd81cecb780fbe35.json` | JSON | data | lens:데이터·ML;type:데이터 | 포함 | - | 2026-01-28T17:51:27 | read-full | last: \[{"doc_key": "guide", "effective_date": "2025-01-08", "doc_id": "guide:2025-01-08#1", "content": "hello world", "source" | JSON file: list\[2\] | 내부 |
| `./data/cache/versioned_pdf/953faf21ee8abc6bf22bad3942b772310ee2e190.json` | JSON | data | lens:데이터·ML;type:데이터 | 포함 | - | 2026-01-28T17:51:27 | read-full | last: \[{"doc_key": "guide", "effective_date": "2025-01-08", "doc_id": "guide:2025-01-08#1", "content": "hello world", "source" | JSON file: list\[2\] | 내부 |
| `./data/cache/versioned_pdf/966d2e8bd1cba9bdabba4e1f6d0f20918770bbe4.json` | JSON | data | lens:데이터·ML;type:데이터 | 포함 | - | 2026-01-28T17:51:27 | read-full | last: \[{"doc_key": "guide", "effective_date": "2025-01-08", "doc_id": "guide:2025-01-08#1", "content": "hello world", "source" | JSON file: list\[2\] | 내부 |
| `./data/cache/versioned_pdf/97f30d96b6ef13e99a2d602cab55d578d40a99a8.json` | JSON | data | lens:데이터·ML;type:데이터 | 포함 | - | 2026-01-28T17:51:27 | read-full | last: \[{"doc_key": "guide", "effective_date": "2025-01-08", "doc_id": "guide:2025-01-08#1", "content": "hello world", "source" | JSON file: list\[2\] | 내부 |
| `./data/cache/versioned_pdf/98f19d1962e682ba3ae3bf699ce16b055795a220.json` | JSON | data | lens:데이터·ML;type:데이터 | 포함 | - | 2026-01-28T17:51:27 | read-full | last: \[{"doc_key": "guide", "effective_date": "2025-01-08", "doc_id": "guide:2025-01-08#1", "content": "hello world", "source" | JSON file: list\[2\] | 내부 |
| `./data/cache/versioned_pdf/cd2b2b985a159b4d7c6b63e0b87cc0391717666e.json` | JSON | data | lens:데이터·ML;type:데이터 | 포함 | - | 2026-01-28T17:51:27 | read-full | last: \[{"doc_key": "guide", "effective_date": "2025-01-08", "doc_id": "guide:2025-01-08#1", "content": "hello world", "source" | JSON file: list\[2\] | 내부 |
| `./data/cache/versioned_pdf/cf4ee9227919437d72f52b9c61fc0eb55d64a386.json` | JSON | data | lens:데이터·ML;type:데이터 | 포함 | - | 2026-01-28T17:51:27 | read-full | last: \[{"doc_key": "guide", "effective_date": "2025-01-08", "doc_id": "guide:2025-01-08#1", "content": "hello world", "source" | JSON file: list\[2\] | 내부 |
| `./data/cache/versioned_pdf/d0f351eaf1bd4192e25b9544e5623f0661627c25.json` | JSON | data | lens:데이터·ML;type:데이터 | 포함 | - | 2026-01-28T17:51:27 | read-full | last: \[{"doc_key": "guide", "effective_date": "2025-01-08", "doc_id": "guide:2025-01-08#1", "content": "hello world", "source" | JSON file: list\[2\] | 내부 |
| `./data/cache/versioned_pdf/d68cb665a21d569119a805b1942425e26e59f572.json` | JSON | data | lens:데이터·ML;type:데이터 | 포함 | - | 2026-01-28T17:51:27 | read-full | last: \[{"doc_key": "guide", "effective_date": "2025-01-08", "doc_id": "guide:2025-01-08#1", "content": "hello world", "source" | JSON file: list\[2\] | 내부 |
| `./data/cache/versioned_pdf/de9ef0c97fd0401dca998183c7e3bce18c5a163f.json` | JSON | data | lens:데이터·ML;type:데이터 | 포함 | - | 2026-01-28T17:51:27 | read-full | last: \[{"doc_key": "guide", "effective_date": "2025-01-08", "doc_id": "guide:2025-01-08#1", "content": "hello world", "source" | JSON file: list\[2\] | 내부 |
| `./data/cache/versioned_pdf/f35f04a19b38aaf8ce2aa7a9dd9596e96af0e9cf.json` | JSON | data | lens:데이터·ML;type:데이터 | 포함 | - | 2026-01-28T17:51:27 | read-full | last: \[{"doc_key": "guide", "effective_date": "2025-01-08", "doc_id": "guide:2025-01-08#1", "content": "hello world", "source" | JSON file: list\[2\] | 내부 |
| `./data/cache/versioned_pdf/fef39322cf49f48dbdf293f7fcbedbdefdb62696.json` | JSON | data | lens:데이터·ML;type:데이터 | 포함 | - | 2026-01-28T17:51:27 | read-full | last: \[{"doc_key": "guide", "effective_date": "2025-01-08", "doc_id": "guide:2025-01-08#1", "content": "hello world", "source" | JSON file: list\[2\] | 내부 |
| `./data/datasets/dummy_test_dataset.json` | JSON | data | lens:데이터·ML;type:데이터 | 포함 | - | 2026-01-28T17:51:27 | read-full | last: {"test": "data"} | JSON file: keys: test | 내부 |
| `./data/datasets/insurance_qa_korean.csv` | CSV | data | lens:데이터·ML;type:데이터 | 포함 | - | 2026-01-28T17:51:27 | read-full | last: kr-005,입원비 보장은 어떻게 되나요?,질병 입원 시 1일당 5만원의 입원비가 지급됩니다.,"\[""질병으로 인한 입원 시 1일당 5만원(최대 180일)이 지급됩니다."",""상해로 인한 입원은 별도의 상해입원비 | CSV file: insurance_qa_korean.csv | 내부 |
| `./data/datasets/insurance_qa_korean.json` | JSON | data | lens:데이터·ML;type:데이터 | 포함 | - | 2026-01-28T17:51:27 | read-full | last: } | JSON file: keys: name,version,thresholds,test_cases | 내부 |
| `./data/datasets/insurance_qa_korean_2.json` | JSON | data | lens:데이터·ML;type:데이터 | 포함 | - | 2026-01-28T17:51:27 | read-full | last: } | JSON file: keys: version,thresholds,name,test_cases | 내부 |
| `./data/datasets/insurance_qa_korean_3.json` | JSON | data | lens:데이터·ML;type:데이터 | 포함 | - | 2026-01-28T17:51:27 | read-full | last: } | JSON file: keys: version,thresholds,name,test_cases | 내부 |
| `./data/datasets/ragas_ko90_en10.json` | JSON | data | lens:데이터·ML;type:데이터 | 포함 | - | 2026-01-28T17:51:27 | read-full | last: } | JSON file: keys: name,version,thresholds,test_cases | 내부 |
| `./data/datasets/sample.json` | JSON | data | lens:데이터·ML;type:데이터 | 포함 | - | 2026-01-28T17:51:27 | read-full | last: } | JSON file: keys: name,version,test_cases | 내부 |
| `./data/datasets/visualization_20q_cluster_map.csv` | CSV | data | lens:데이터·ML;type:데이터 | 포함 | - | 2026-01-28T17:51:27 | read-full | last: vis-020,4 | CSV file: visualization_20q_cluster_map.csv | 내부 |
| `./data/datasets/visualization_20q_korean.json` | JSON | data | lens:데이터·ML;type:데이터 | 포함 | - | 2026-01-28T17:51:27 | read-full | last: } | JSON file: keys: name,version,description,metadata,thresholds,test_cases | 내부 |
| `./data/datasets/visualization_2q_cluster_map.csv` | CSV | data | lens:데이터·ML;type:데이터 | 포함 | - | 2026-01-28T17:51:27 | read-full | last: vis-006,2 | CSV file: visualization_2q_cluster_map.csv | 내부 |
| `./data/datasets/visualization_2q_korean.json` | JSON | data | lens:데이터·ML;type:데이터 | 포함 | - | 2026-01-28T17:51:27 | read-full | last: } | JSON file: keys: name,version,description,metadata,thresholds,test_cases | 내부 |
| `./data/db/evalvault.db` | DB | data | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./data/db/evalvault_memory.db` | DB | data | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./data/db/evalvault_run_0019083a-ed7a-4448-b074-ee259013c671.xlsx` | XLSX | data | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./data/db/evalvault_run_00ee0353-5544-44ca-b018-e0f0265f2867.xlsx` | XLSX | data | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./data/db/evalvault_run_01ccc9fd-d670-4337-a2d5-a5cbff334916.xlsx` | XLSX | data | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./data/db/evalvault_run_01da597b-aded-488a-8f58-877f373bc09f.xlsx` | XLSX | data | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./data/db/evalvault_run_01ffa508-0a8f-4451-9249-c44666b337c6.xlsx` | XLSX | data | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./data/db/evalvault_run_026a47a9-c373-4cbb-8f1d-bee004df2928.xlsx` | XLSX | data | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./data/db/evalvault_run_03ab7fd0-fc70-4d82-86dd-05096f914d7a.xlsx` | XLSX | data | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./data/db/evalvault_run_04da6d5c-def9-4b98-b9b9-04dafcda5300.xlsx` | XLSX | data | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./data/db/evalvault_run_0528d7a0-3324-4c91-b02f-88e9a1d01c8b.xlsx` | XLSX | data | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./data/db/evalvault_run_05aacc61-9502-4ebc-b211-8bfd10d1d041.xlsx` | XLSX | data | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./data/db/evalvault_run_077aa840-cf9c-4d9c-a30c-2267fed627d3.xlsx` | XLSX | data | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./data/db/evalvault_run_090eb89a-8b1d-475e-a1f2-a4b247d3cae7.xlsx` | XLSX | data | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./data/db/evalvault_run_0bc819c3-6509-43be-9134-9256b7f141ca.xlsx` | XLSX | data | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./data/db/evalvault_run_0c0515df-9c45-4100-8e09-3bc2f7aae0fc.xlsx` | XLSX | data | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./data/db/evalvault_run_0c4e97b2-4379-49f1-9ba1-56cd2d7ac562.xlsx` | XLSX | data | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./data/db/evalvault_run_0d874126-3ac3-48e1-a108-e351c54ebcca.xlsx` | XLSX | data | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./data/db/evalvault_run_0dc932d9-8f3a-42f0-8717-40a92998f3bf.xlsx` | XLSX | data | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./data/db/evalvault_run_101ada34-920a-494b-9956-8b853145ec1b.xlsx` | XLSX | data | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./data/db/evalvault_run_108db8b1-a826-4dea-948c-30428b0095da.xlsx` | XLSX | data | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./data/db/evalvault_run_10ce749c-a3dd-4997-aaf6-19920c2572e7.xlsx` | XLSX | data | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./data/db/evalvault_run_1115c9b2-0c59-40b7-8c27-9b6e766b72eb.xlsx` | XLSX | data | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./data/db/evalvault_run_127860f3-3ca6-41f6-86f7-b193d9e201a1.xlsx` | XLSX | data | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./data/db/evalvault_run_12a9d971-5af0-45a7-9c37-de244a730676.xlsx` | XLSX | data | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./data/db/evalvault_run_12d9a740-4003-43fd-a440-12d7d6a63a6c.xlsx` | XLSX | data | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./data/db/evalvault_run_140e7731-8f12-41ce-ae79-9db0295b468f.xlsx` | XLSX | data | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./data/db/evalvault_run_145cb83f-58ab-469f-8fe6-c06a07c865aa.xlsx` | XLSX | data | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./data/db/evalvault_run_1507a374-91e1-4764-a8d1-0d5642dc091f.xlsx` | XLSX | data | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./data/db/evalvault_run_16072517-6277-4b1b-a192-c3b4f0af8147.xlsx` | XLSX | data | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./data/db/evalvault_run_17471c5f-ce27-4d29-a2b2-56cc5d79ef88.xlsx` | XLSX | data | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./data/db/evalvault_run_17e8542c-8684-440a-be31-8e411ed3cc0a.xlsx` | XLSX | data | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./data/db/evalvault_run_1946e831-2eef-434e-919d-3e3fb0d91967.xlsx` | XLSX | data | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./data/db/evalvault_run_197ecbfe-6810-4fe1-a579-ee1f66bce2d1.xlsx` | XLSX | data | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./data/db/evalvault_run_1a0e1493-2769-4755-91e4-6bd140d4fc4c.xlsx` | XLSX | data | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./data/db/evalvault_run_1aa2548a-3411-4ba6-a177-3789fa3ea9cf.xlsx` | XLSX | data | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./data/db/evalvault_run_1cab28c9-d30f-4394-af1c-2441b05811e8.xlsx` | XLSX | data | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./data/db/evalvault_run_1cacac34-a49b-4bf1-9ebe-325fa4d4fb40.xlsx` | XLSX | data | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./data/db/evalvault_run_1d150bb2-e5c8-40e6-a282-6d0799fc5427.xlsx` | XLSX | data | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./data/db/evalvault_run_1e940662-8be4-4aae-987d-bba7e22ff526.xlsx` | XLSX | data | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./data/db/evalvault_run_1fb14e94-cffc-41fd-9ee0-b1618fdad4cf.xlsx` | XLSX | data | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./data/db/evalvault_run_1fca88f2-0230-4102-8b0a-23753df6fb0e.xlsx` | XLSX | data | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./data/db/evalvault_run_20461915-04b9-49a8-a702-2757bfeeceb5.xlsx` | XLSX | data | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./data/db/evalvault_run_20d63902-ed3b-4660-8f69-97419617ff59.xlsx` | XLSX | data | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./data/db/evalvault_run_215d4792-cba4-4cb4-b4f6-5db9c85ec392.xlsx` | XLSX | data | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./data/db/evalvault_run_233aa11e-4c66-4fc8-971f-a5583f523d7e.xlsx` | XLSX | data | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./data/db/evalvault_run_23594bfc-a3f5-4d1d-b269-d95478d2507e.xlsx` | XLSX | data | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./data/db/evalvault_run_2588858c-4d61-4d93-af18-9bdbeab73872.xlsx` | XLSX | data | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./data/db/evalvault_run_29534005-135e-4fd2-87e2-10775fa18c9c.xlsx` | XLSX | data | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./data/db/evalvault_run_2a26a2ce-bdb8-44d0-8612-0130d78552d2.xlsx` | XLSX | data | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./data/db/evalvault_run_2b56bfbb-0117-48ce-b39d-188280d94ead.xlsx` | XLSX | data | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./data/db/evalvault_run_2bc07198-614d-4931-9bee-a6cf912267f8.xlsx` | XLSX | data | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./data/db/evalvault_run_2c334602-0a5d-4123-9656-bd3a7cee932b.xlsx` | XLSX | data | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./data/db/evalvault_run_2c67bc66-56c3-4b72-a463-ce880f52fdf4.xlsx` | XLSX | data | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./data/db/evalvault_run_2ce54d3c-95cc-44f9-9289-727fa287d4e2.xlsx` | XLSX | data | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./data/db/evalvault_run_2d5a89fb-deae-4dae-8748-a0104f0a9ce3.xlsx` | XLSX | data | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./data/db/evalvault_run_2db07d07-faad-4d7e-9c16-f8d173b6aded.xlsx` | XLSX | data | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./data/db/evalvault_run_2de05b2c-6ce5-4803-86db-6979d74c9c1e.xlsx` | XLSX | data | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./data/db/evalvault_run_2e495f28-020f-4a64-a644-b136c1e8839e.xlsx` | XLSX | data | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./data/db/evalvault_run_2e8b9463-7304-41be-88a2-ac92aa3abfbb.xlsx` | XLSX | data | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./data/db/evalvault_run_2ec038a5-efed-4cee-985f-26c67d6773b6.xlsx` | XLSX | data | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./data/db/evalvault_run_2fbbd4de-bdff-45f0-a15a-88ae151d5256.xlsx` | XLSX | data | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./data/db/evalvault_run_2fd24aa8-a827-46bc-83b3-fd4e121f9e1d.xlsx` | XLSX | data | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./data/db/evalvault_run_3072ca61-42f1-489f-881e-becc1ced6504.xlsx` | XLSX | data | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./data/db/evalvault_run_31375ae8-09f6-4827-a5a8-68646b168874.xlsx` | XLSX | data | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./data/db/evalvault_run_3156966d-39cb-424d-bec6-b7d4a055448e.xlsx` | XLSX | data | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./data/db/evalvault_run_32be84d5-88bd-4844-b5b5-3776232dd9c9.xlsx` | XLSX | data | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./data/db/evalvault_run_33505410-7148-4101-bb15-e35784d1705f.xlsx` | XLSX | data | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./data/db/evalvault_run_34aba331-407f-49ca-9912-8d403cc8db9c.xlsx` | XLSX | data | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./data/db/evalvault_run_3584d1be-2577-46ef-b861-59db7ead5d5a.xlsx` | XLSX | data | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./data/db/evalvault_run_3595d7ea-66c5-4064-a912-4ab5e0c4bf5d.xlsx` | XLSX | data | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./data/db/evalvault_run_368eb1d3-1a15-4117-9740-f6885827c803.xlsx` | XLSX | data | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./data/db/evalvault_run_36b5011d-ad72-4cfa-aaa3-bc69004ef244.xlsx` | XLSX | data | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./data/db/evalvault_run_3787d433-e141-42ee-9860-469dee0aadef.xlsx` | XLSX | data | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./data/db/evalvault_run_37942d43-2843-4d5c-ab61-fbd31cfe16ea.xlsx` | XLSX | data | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./data/db/evalvault_run_37c6f7d5-7811-45b9-b9fe-980cc0c18f13.xlsx` | XLSX | data | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./data/db/evalvault_run_37d298a7-cebc-4d0e-99b5-d3ca88544aae.xlsx` | XLSX | data | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./data/db/evalvault_run_388ac7c6-2d24-4fcc-8ef3-86f8f24eb6ea.xlsx` | XLSX | data | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./data/db/evalvault_run_38aae8ba-6e3b-496f-8a23-f3d7dfef93f2.xlsx` | XLSX | data | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./data/db/evalvault_run_38d67d7f-befb-4d6f-b075-16606234e7f8.xlsx` | XLSX | data | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./data/db/evalvault_run_3b0820ad-d16f-4ef3-994b-4253f490a626.xlsx` | XLSX | data | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./data/db/evalvault_run_3b578f84-5c45-4f13-a993-71de27028991.xlsx` | XLSX | data | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./data/db/evalvault_run_3ca7d049-67d0-4da4-b3bc-7a17ea4c537c.xlsx` | XLSX | data | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./data/db/evalvault_run_3cf354a9-8132-4a78-81ee-e1cab277b52c.xlsx` | XLSX | data | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./data/db/evalvault_run_3d30147a-bef2-4eb7-a2ab-790a1330325d.xlsx` | XLSX | data | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./data/db/evalvault_run_3d47835e-ed78-4103-b2f9-b811e455bcd1.xlsx` | XLSX | data | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./data/db/evalvault_run_3d8c1565-7a1c-4ada-b00a-2656089f72f3.xlsx` | XLSX | data | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./data/db/evalvault_run_3e0e8ff1-aa20-4578-9654-90a7be934c25.xlsx` | XLSX | data | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./data/db/evalvault_run_3eead056-9c9c-4a97-8525-7f5ab152707a.xlsx` | XLSX | data | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./data/db/evalvault_run_3fd6e25f-e906-421d-a37d-fde31d876aac.xlsx` | XLSX | data | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./data/db/evalvault_run_41efcecd-c478-404b-9e2d-2346b39128b4.xlsx` | XLSX | data | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./data/db/evalvault_run_41fac1d1-18dc-4051-8ca0-ea584a6ad24f.xlsx` | XLSX | data | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./data/db/evalvault_run_4250bf07-5e06-493f-a26a-ca8a26ace9c9.xlsx` | XLSX | data | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./data/db/evalvault_run_433717ad-3279-40d8-9ff9-122371198bd6.xlsx` | XLSX | data | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./data/db/evalvault_run_4365d376-126f-456d-b11c-6faefcdc1b89.xlsx` | XLSX | data | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./data/db/evalvault_run_47125eec-9ed5-4d5f-921c-1af8acf45d09.xlsx` | XLSX | data | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./data/db/evalvault_run_476e1abd-45c7-404a-b698-a18578bf5f65.xlsx` | XLSX | data | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./data/db/evalvault_run_48b72052-dba9-4771-a442-b192a2da2927.xlsx` | XLSX | data | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./data/db/evalvault_run_48c94f63-6ad8-4a65-9652-7a7d06472c86.xlsx` | XLSX | data | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./data/db/evalvault_run_49961f02-6659-41ea-9b6e-30db3fddca7b.xlsx` | XLSX | data | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./data/db/evalvault_run_49cdc6a1-6945-409a-98f0-9e2fa35d8d54.xlsx` | XLSX | data | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./data/db/evalvault_run_49dec022-9240-49f8-abb8-0de5cdd932c2.xlsx` | XLSX | data | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./data/db/evalvault_run_4a268eef-4b1b-4102-b407-1cf6fd00bf53.xlsx` | XLSX | data | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./data/db/evalvault_run_4a8e8a52-b2a7-40af-8639-620fb64f74a7.xlsx` | XLSX | data | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./data/db/evalvault_run_4a9795b0-1bea-45a3-80cb-3a0209d5b186.xlsx` | XLSX | data | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./data/db/evalvault_run_4b2cbcad-2162-4745-840c-68411b5d7cd4.xlsx` | XLSX | data | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./data/db/evalvault_run_4b6f8fc8-046e-457a-9004-176fd1b25ec5.xlsx` | XLSX | data | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./data/db/evalvault_run_4c897121-acca-478c-a084-1aece48d5aba.xlsx` | XLSX | data | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./data/db/evalvault_run_4d194db0-085f-491d-bf53-4f54a20fe128.xlsx` | XLSX | data | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./data/db/evalvault_run_4d2a17a0-5990-4133-a1d0-9a8f14028fd9.xlsx` | XLSX | data | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./data/db/evalvault_run_4dc8af27-bae8-4a5c-9b1e-c57b1402a2f4.xlsx` | XLSX | data | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./data/db/evalvault_run_4e336103-5983-4e09-a0aa-74926ef36905.xlsx` | XLSX | data | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./data/db/evalvault_run_4f0a6373-091e-45d4-9e65-c96b539b1350.xlsx` | XLSX | data | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./data/db/evalvault_run_4f2d9b36-a76e-4208-873b-b5c6b14e2795.xlsx` | XLSX | data | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./data/db/evalvault_run_4f4a3985-07c5-4bcc-892e-08c652424604.xlsx` | XLSX | data | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./data/db/evalvault_run_502851c0-cc95-48ac-befb-ff7178f6a8b5.xlsx` | XLSX | data | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./data/db/evalvault_run_521b1eaf-8f38-4f32-943e-782193ba6f31.xlsx` | XLSX | data | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./data/db/evalvault_run_5297ad43-c3c0-48d0-99ef-5795bc723a70.xlsx` | XLSX | data | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./data/db/evalvault_run_52d13133-4e4a-47de-85e0-b82a2c051171.xlsx` | XLSX | data | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./data/db/evalvault_run_536351b5-b622-45d9-8338-eb45f95db876.xlsx` | XLSX | data | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./data/db/evalvault_run_53ab1f6b-5f09-4837-b361-5860539c5a64.xlsx` | XLSX | data | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./data/db/evalvault_run_546a8b8f-16e6-43d9-924d-8e653d6d62d2.xlsx` | XLSX | data | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./data/db/evalvault_run_5601ed41-435b-4214-8e9d-97bb4797642c.xlsx` | XLSX | data | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./data/db/evalvault_run_562e7ecf-74c9-4b33-8ce5-dca73f8e0bea.xlsx` | XLSX | data | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./data/db/evalvault_run_57c09f5d-bfb9-4014-9e04-ba7acee550c4.xlsx` | XLSX | data | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./data/db/evalvault_run_59b6c49a-234f-4271-910e-40dcccb3b6b1.xlsx` | XLSX | data | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./data/db/evalvault_run_5a32bde9-292b-4a77-82f9-a2abc02f1110.xlsx` | XLSX | data | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./data/db/evalvault_run_5b6917f8-6601-4034-8adc-03ea1312a505.xlsx` | XLSX | data | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./data/db/evalvault_run_5be2356e-44b1-4f16-8680-0de9ff30d0e0.xlsx` | XLSX | data | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./data/db/evalvault_run_5c0050b2-424a-47f5-9430-9cb60c6c1ff8.xlsx` | XLSX | data | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./data/db/evalvault_run_5c161ec3-e8df-4939-8458-27594dea27e9.xlsx` | XLSX | data | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./data/db/evalvault_run_5c24d14e-ae4e-460b-a6bd-ed4e6f16b64e.xlsx` | XLSX | data | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./data/db/evalvault_run_5c5522e7-55fa-4c91-8a2a-257449afcf26.xlsx` | XLSX | data | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./data/db/evalvault_run_5d40602b-6570-4ba2-9b1d-85f4a06f68ae.xlsx` | XLSX | data | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./data/db/evalvault_run_5da68fb5-c012-46e4-a4f8-92d88f06fdab.xlsx` | XLSX | data | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./data/db/evalvault_run_5e55330f-5888-4645-8d5b-35db58c0fb6a.xlsx` | XLSX | data | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./data/db/evalvault_run_5e9f41bd-94c4-4cbd-aec0-3c713ebd7c96.xlsx` | XLSX | data | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./data/db/evalvault_run_5f74185a-d738-4ba5-90ff-7cd9ec26ee55.xlsx` | XLSX | data | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./data/db/evalvault_run_60e3865f-8c89-4634-a061-90085de90802.xlsx` | XLSX | data | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./data/db/evalvault_run_60e68d09-6b69-45ae-8005-c1e5431a39e9.xlsx` | XLSX | data | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./data/db/evalvault_run_60f04945-14f2-4905-8cc0-247db30669b0.xlsx` | XLSX | data | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./data/db/evalvault_run_624bbcdf-9013-40b9-afd8-263f70199509.xlsx` | XLSX | data | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./data/db/evalvault_run_626d56df-d716-4dee-9065-b5938ab44623.xlsx` | XLSX | data | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./data/db/evalvault_run_62e2b274-448f-456c-88c7-cc68b2ab025c.xlsx` | XLSX | data | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./data/db/evalvault_run_64486cbc-921b-4ca1-9f79-5819e8a04c7c.xlsx` | XLSX | data | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./data/db/evalvault_run_648f2371-6efe-4667-8af6-89dd6d8fcb03.xlsx` | XLSX | data | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./data/db/evalvault_run_64c9f997-1ba9-485c-a213-dfd1b41067c3.xlsx` | XLSX | data | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./data/db/evalvault_run_651bcd16-464f-42d3-a539-f4d18de9f5c5.xlsx` | XLSX | data | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./data/db/evalvault_run_6526ff1c-2ada-4ff1-8146-d34bec69a711.xlsx` | XLSX | data | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./data/db/evalvault_run_660592a6-6717-4ef7-8bb9-f4a1f4d7d1d6.xlsx` | XLSX | data | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./data/db/evalvault_run_660a9c2b-d037-4986-b1e1-0b0a443e0ee9.xlsx` | XLSX | data | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./data/db/evalvault_run_664812d8-d918-4c44-b473-b330aa56a5b4.xlsx` | XLSX | data | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./data/db/evalvault_run_667b4443-77da-4c28-9676-701e14048edf.xlsx` | XLSX | data | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./data/db/evalvault_run_66992edf-b380-4411-84fa-ad71f95425f9.xlsx` | XLSX | data | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./data/db/evalvault_run_66b8793d-5106-4831-a63b-6fe814a1178a.xlsx` | XLSX | data | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./data/db/evalvault_run_67422936-c498-44f3-a812-2d0fbd08d6bb.xlsx` | XLSX | data | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./data/db/evalvault_run_67dea70b-32bf-457c-98b9-3190151eb6b6.xlsx` | XLSX | data | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./data/db/evalvault_run_67e154c3-8481-4126-a900-d4564c3207c7.xlsx` | XLSX | data | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./data/db/evalvault_run_6813b46a-3322-4867-91bd-2018b1ea5e9b.xlsx` | XLSX | data | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./data/db/evalvault_run_68c1dfe5-9dfb-47bf-852c-1252ed2381f5.xlsx` | XLSX | data | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./data/db/evalvault_run_69efa4c9-dbc6-4e6a-91da-14ac1b4ca0aa.xlsx` | XLSX | data | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./data/db/evalvault_run_6b5ac263-90fc-4ee1-a0c9-ead6aedc1bc1.xlsx` | XLSX | data | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./data/db/evalvault_run_6d825c11-7786-4db1-8e69-fa1641526383.xlsx` | XLSX | data | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./data/db/evalvault_run_6d9dedd0-b38c-439e-a1d0-c29d4e2e4a8e.xlsx` | XLSX | data | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./data/db/evalvault_run_6df68d64-0d8e-4ca0-8195-f4631df3c4b1.xlsx` | XLSX | data | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./data/db/evalvault_run_6f54e407-1e47-4909-9044-698d26bdccf0.xlsx` | XLSX | data | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./data/db/evalvault_run_7002a2ae-32f5-4e23-a84b-cd8918008497.xlsx` | XLSX | data | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./data/db/evalvault_run_7023b35b-ff13-4cfc-b93d-a6491137bdab.xlsx` | XLSX | data | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./data/db/evalvault_run_70e81f18-a73b-498d-b365-af947c903107.xlsx` | XLSX | data | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./data/db/evalvault_run_7119085a-2e71-4ad6-8700-80182906b6e7.xlsx` | XLSX | data | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./data/db/evalvault_run_72b30abe-9bfa-400b-a657-a1656c4e0902.xlsx` | XLSX | data | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./data/db/evalvault_run_730f89b6-7623-4405-9939-83acf94bf2d2.xlsx` | XLSX | data | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./data/db/evalvault_run_73e8b2f5-f54d-408b-b8db-465cd5d95d92.xlsx` | XLSX | data | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./data/db/evalvault_run_73f974a2-91fd-4560-9881-b33d706fd269.xlsx` | XLSX | data | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./data/db/evalvault_run_745f7188-a243-4d56-98b8-09b278cea6b7.xlsx` | XLSX | data | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./data/db/evalvault_run_746ef4f6-4e89-4dca-a040-e5d7b6e40299.xlsx` | XLSX | data | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./data/db/evalvault_run_747dfb20-6e5f-4f07-956a-06e611f4454d.xlsx` | XLSX | data | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./data/db/evalvault_run_74820c60-319f-482f-90fc-30d13b3e8b2d.xlsx` | XLSX | data | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./data/db/evalvault_run_758ab90e-f8ea-4410-9923-d75d7448a4c2.xlsx` | XLSX | data | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./data/db/evalvault_run_76bf9307-b4d5-4a49-98fd-6532bbec4d2f.xlsx` | XLSX | data | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./data/db/evalvault_run_779ae0ab-0e56-4f9b-87e1-c0b6349e81fa.xlsx` | XLSX | data | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./data/db/evalvault_run_77af727c-3f66-4536-a871-2683fd1ee0a0.xlsx` | XLSX | data | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./data/db/evalvault_run_7879bb40-6c11-403b-894b-b0c397081f0f.xlsx` | XLSX | data | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./data/db/evalvault_run_78e6cd0e-43fb-46dd-b182-e12887bf8bb4.xlsx` | XLSX | data | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./data/db/evalvault_run_7ae91110-a7b0-49fb-ad0f-f0718ed2b1e4.xlsx` | XLSX | data | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./data/db/evalvault_run_7b300962-1530-4323-9af2-7fc2bc38f29c.xlsx` | XLSX | data | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./data/db/evalvault_run_7b698ba6-beaf-41d4-85cd-6ae57c54818d.xlsx` | XLSX | data | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./data/db/evalvault_run_7bb5eaa9-dc17-412a-a42b-ba92279b5311.xlsx` | XLSX | data | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./data/db/evalvault_run_7bef1ea7-442e-455f-9c88-e731e37899f5.xlsx` | XLSX | data | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./data/db/evalvault_run_7e72bea6-e786-4e45-b3a7-e6e7ae2a2997.xlsx` | XLSX | data | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./data/db/evalvault_run_7e896e32-28a6-4ac5-93f7-261c1abf9e2c.xlsx` | XLSX | data | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./data/db/evalvault_run_7e9106fc-d2db-4a52-8e31-83214198b3aa.xlsx` | XLSX | data | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./data/db/evalvault_run_7ecb24d8-176e-4efc-9dde-dc6b2865df6a.xlsx` | XLSX | data | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./data/db/evalvault_run_810cc0c8-f467-4ce7-bcaa-660f9cf7efb8.xlsx` | XLSX | data | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./data/db/evalvault_run_83082904-b671-423c-8fda-40ae0014db5f.xlsx` | XLSX | data | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./data/db/evalvault_run_83d38473-2608-4198-a5e7-373c0452d73d.xlsx` | XLSX | data | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./data/db/evalvault_run_83fc84bb-fd66-4db9-975c-a1bfdcecf9d5.xlsx` | XLSX | data | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./data/db/evalvault_run_84ac5d1f-cce7-4540-bf9a-06d5ee42228c.xlsx` | XLSX | data | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./data/db/evalvault_run_84f1de99-01f8-45c9-9f8f-1c4c32b4c44c.xlsx` | XLSX | data | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./data/db/evalvault_run_850c786e-50ec-4b41-b3f6-c726380d8680.xlsx` | XLSX | data | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./data/db/evalvault_run_853664f6-518c-4306-92a1-fc13542d7254.xlsx` | XLSX | data | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./data/db/evalvault_run_854ff79f-2106-4ab0-9b90-32bac55a52e2.xlsx` | XLSX | data | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./data/db/evalvault_run_861e3277-10fe-4f9d-b41c-51f7982bdb73.xlsx` | XLSX | data | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./data/db/evalvault_run_86c2bd5b-88f0-462b-96a8-03ce835cbdf2.xlsx` | XLSX | data | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./data/db/evalvault_run_86e93743-3423-4568-87f4-ca092b4852be.xlsx` | XLSX | data | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./data/db/evalvault_run_871a0361-0168-469e-94bf-046cb04249a0.xlsx` | XLSX | data | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./data/db/evalvault_run_8854fbbd-bd0f-4022-9929-0bac014aa289.xlsx` | XLSX | data | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./data/db/evalvault_run_8a961371-d402-4880-b5e2-9a35bff5a5d4.xlsx` | XLSX | data | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./data/db/evalvault_run_8b015c2e-d8dd-4057-adcc-6197a9da110e.xlsx` | XLSX | data | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./data/db/evalvault_run_8b081bf0-dd04-4170-a09d-04d72d5e420d.xlsx` | XLSX | data | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./data/db/evalvault_run_8b6cf7a1-dfba-4c9c-903b-4aeb0d2d6474.xlsx` | XLSX | data | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./data/db/evalvault_run_8c3bedfd-45f6-4081-b7ba-2ef5c68b0035.xlsx` | XLSX | data | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./data/db/evalvault_run_8c668d4d-2c0d-4d3f-a3c0-79512e56ceb5.xlsx` | XLSX | data | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./data/db/evalvault_run_8cfbb0a4-a79d-4719-a50a-5cb09e0d33f7.xlsx` | XLSX | data | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./data/db/evalvault_run_904ad834-ceff-4909-971c-ae7ccc2238e7.xlsx` | XLSX | data | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./data/db/evalvault_run_942e79c4-58fb-4ce3-9ea6-3f08257c6dc7.xlsx` | XLSX | data | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./data/db/evalvault_run_94491b3e-4c0d-424f-8121-2d76f4324089.xlsx` | XLSX | data | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./data/db/evalvault_run_94a0c74f-6472-4c8c-bfa0-05785565903d.xlsx` | XLSX | data | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./data/db/evalvault_run_95973db8-478d-4529-ad28-5dd5a77f9bf1.xlsx` | XLSX | data | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./data/db/evalvault_run_95add858-0f41-4d1c-a236-b30465ffdb58.xlsx` | XLSX | data | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./data/db/evalvault_run_95d6481c-11d1-44ba-9b93-406b3033c535.xlsx` | XLSX | data | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./data/db/evalvault_run_967c437b-0028-4cec-85ed-7ded9216713d.xlsx` | XLSX | data | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./data/db/evalvault_run_9699dacc-a968-4fe3-a141-fd0efc4ae2ab.xlsx` | XLSX | data | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./data/db/evalvault_run_96b6cf33-f127-44da-bf14-a25442602142.xlsx` | XLSX | data | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./data/db/evalvault_run_97a44e0c-8ea7-48ca-a78c-87a762b6e7de.xlsx` | XLSX | data | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./data/db/evalvault_run_99a42b54-ffe1-4b76-b563-6a02fecee5a9.xlsx` | XLSX | data | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./data/db/evalvault_run_99fce94b-bec1-4f93-a57d-e2500220571d.xlsx` | XLSX | data | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./data/db/evalvault_run_9a08cad0-4187-4b73-b73e-a709daf379b7.xlsx` | XLSX | data | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./data/db/evalvault_run_9a137e92-e773-4016-bc36-a12313087cdb.xlsx` | XLSX | data | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./data/db/evalvault_run_9aa11159-c147-4c62-8314-63ef58a82ce4.xlsx` | XLSX | data | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./data/db/evalvault_run_9d87889c-ee86-40ae-b945-98c16da158c5.xlsx` | XLSX | data | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./data/db/evalvault_run_9dc707fa-8b1c-4c56-b105-6e7bb7bd4f7e.xlsx` | XLSX | data | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./data/db/evalvault_run_9e7ecf86-78ff-4c3c-9f78-471eecc762b8.xlsx` | XLSX | data | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./data/db/evalvault_run_a05f055a-1327-464c-a04e-2317211629b4.xlsx` | XLSX | data | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./data/db/evalvault_run_a0b122ad-dc85-4209-a8c1-b34e14d476d5.xlsx` | XLSX | data | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./data/db/evalvault_run_a0c4fed1-9468-4383-bf8f-2bb679e49430.xlsx` | XLSX | data | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./data/db/evalvault_run_a20f9c82-76bb-4f20-9eac-0dbde35f8d10.xlsx` | XLSX | data | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./data/db/evalvault_run_a2289511-6689-406f-9a8e-b159d04e72b7.xlsx` | XLSX | data | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./data/db/evalvault_run_a40f6f4f-b237-4bfe-92d7-10119473e920.xlsx` | XLSX | data | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./data/db/evalvault_run_a5b43855-b5b1-443c-a9f8-4490447370ea.xlsx` | XLSX | data | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./data/db/evalvault_run_a6abc2a8-a6ce-46f8-ae81-231ebf1d179a.xlsx` | XLSX | data | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./data/db/evalvault_run_a6f72d11-bd87-4759-ac04-6e7e8147408e.xlsx` | XLSX | data | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./data/db/evalvault_run_a6f86cba-85a9-487d-b654-5e9e9e30c8db.xlsx` | XLSX | data | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./data/db/evalvault_run_a75281a8-0f36-4337-b526-ace22273466a.xlsx` | XLSX | data | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./data/db/evalvault_run_a77d8761-13cb-497c-8cc7-7ce17cbb70b5.xlsx` | XLSX | data | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./data/db/evalvault_run_a95048fc-428e-4263-92c7-9c7417827212.xlsx` | XLSX | data | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./data/db/evalvault_run_a9fd1bc1-f095-4917-96be-bf8e28ed7d76.xlsx` | XLSX | data | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./data/db/evalvault_run_aa4828b5-f36f-4f12-acac-15c551f3b70a.xlsx` | XLSX | data | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./data/db/evalvault_run_aabb43e8-6594-4389-83d9-7c7ce77355c3.xlsx` | XLSX | data | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./data/db/evalvault_run_aadbc07a-0d5a-4175-b273-76303e679512.xlsx` | XLSX | data | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./data/db/evalvault_run_aae53482-87ff-4330-b9f5-d1a264e929af.xlsx` | XLSX | data | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./data/db/evalvault_run_ab379baa-0cee-447c-baee-98acf765bc5b.xlsx` | XLSX | data | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./data/db/evalvault_run_abb9ec61-4d4d-4afd-8473-c3f0b18c1d9f.xlsx` | XLSX | data | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./data/db/evalvault_run_ac0c8f32-8b39-41a4-8992-38e0f35e5c37.xlsx` | XLSX | data | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./data/db/evalvault_run_ad31d518-6e2c-4cfb-8307-62a08e23c5b1.xlsx` | XLSX | data | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./data/db/evalvault_run_ade8a795-ebd1-410d-9751-f75711d71339.xlsx` | XLSX | data | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./data/db/evalvault_run_b01ec923-3249-40a4-b8ad-71c432b10cc7.xlsx` | XLSX | data | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./data/db/evalvault_run_b069b54c-7bc4-4f44-a5c8-150cc7f4cccb.xlsx` | XLSX | data | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./data/db/evalvault_run_b44d33c6-4e63-463f-af1c-f36ebed9ac1c.xlsx` | XLSX | data | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./data/db/evalvault_run_b5227c3f-4b73-44a0-98a9-b470e0c8c7ae.xlsx` | XLSX | data | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./data/db/evalvault_run_b577afcc-2bfe-429f-9b74-03a338444702.xlsx` | XLSX | data | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./data/db/evalvault_run_b5b4d80f-2062-464b-b4fd-8aed94cf1ab0.xlsx` | XLSX | data | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./data/db/evalvault_run_b6058a48-66b9-484e-a100-12d821ea7d99.xlsx` | XLSX | data | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./data/db/evalvault_run_b64f5698-9449-4405-9314-8138a72e75fc.xlsx` | XLSX | data | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./data/db/evalvault_run_b766a211-d778-47a6-84ae-68dbddbf6246.xlsx` | XLSX | data | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./data/db/evalvault_run_ba7a5414-da9c-4889-8838-9dd839b94b78.xlsx` | XLSX | data | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./data/db/evalvault_run_ba8b9fae-dfc6-4800-a762-c03bcb78508f.xlsx` | XLSX | data | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./data/db/evalvault_run_bab778e9-2b6d-47bb-b0de-b5b4cce67466.xlsx` | XLSX | data | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./data/db/evalvault_run_bb4d8f3d-30c0-4b67-8869-760c5c57b744.xlsx` | XLSX | data | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./data/db/evalvault_run_bcadc2fb-6b4f-4ec3-9bab-53a664b3efaa.xlsx` | XLSX | data | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./data/db/evalvault_run_c058ed76-dd7a-4942-8aeb-d74f3952c057.xlsx` | XLSX | data | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./data/db/evalvault_run_c14f98a4-f449-4350-8f7a-0468f2564dfd.xlsx` | XLSX | data | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./data/db/evalvault_run_c186197d-75ac-4627-9447-884ed033a5ec.xlsx` | XLSX | data | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./data/db/evalvault_run_c19b44eb-784c-4104-8eba-3662668b0095.xlsx` | XLSX | data | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./data/db/evalvault_run_c1dd89bc-9f5d-401f-b281-d8fcb1cdf981.xlsx` | XLSX | data | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./data/db/evalvault_run_c28ebffb-497f-4c1f-b663-fee1299dab9f.xlsx` | XLSX | data | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./data/db/evalvault_run_c3307ab7-899d-40e4-910b-3d72812a52fd.xlsx` | XLSX | data | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./data/db/evalvault_run_c3b3042c-0ab5-4291-906a-0a94a74db0b2.xlsx` | XLSX | data | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./data/db/evalvault_run_c3f77310-49b3-4001-8ea6-f1c89dafceaa.xlsx` | XLSX | data | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./data/db/evalvault_run_c42e95b5-735c-4439-87d9-c86df4720443.xlsx` | XLSX | data | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./data/db/evalvault_run_c4ada3ab-d335-42f1-ac38-bc4f1e0e6273.xlsx` | XLSX | data | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./data/db/evalvault_run_c4bbc9e9-054f-4840-a21d-fcd978a8fb16.xlsx` | XLSX | data | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./data/db/evalvault_run_c4fceb0c-c5e4-49ab-814e-8f7de2d2e962.xlsx` | XLSX | data | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./data/db/evalvault_run_c5729e79-a9f6-467f-be42-6057717183ff.xlsx` | XLSX | data | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./data/db/evalvault_run_c595ac87-172f-49aa-97d9-52229b37361e.xlsx` | XLSX | data | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./data/db/evalvault_run_c9625017-701a-4a93-9daf-3e3cbeb7dce1.xlsx` | XLSX | data | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./data/db/evalvault_run_ca6b1796-585a-4166-9546-e34c22386c2c.xlsx` | XLSX | data | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./data/db/evalvault_run_cb25200f-20ff-4232-a8a9-cfc1bede313b.xlsx` | XLSX | data | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./data/db/evalvault_run_cb49db2f-63bc-4d6e-8339-4461d0b9eff1.xlsx` | XLSX | data | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./data/db/evalvault_run_cb66237c-9ae0-4e21-8049-4d27e55c95f9.xlsx` | XLSX | data | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./data/db/evalvault_run_cbb8a2d0-7b89-4bf7-8ccb-b53ddf1e6a5f.xlsx` | XLSX | data | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./data/db/evalvault_run_ccabf600-18c3-4bc3-94fd-552804476277.xlsx` | XLSX | data | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./data/db/evalvault_run_cd2f2379-02ce-4f50-928d-03d127281f8d.xlsx` | XLSX | data | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./data/db/evalvault_run_cd72dc08-a020-4745-b30f-d7dc8085c7d2.xlsx` | XLSX | data | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./data/db/evalvault_run_cde5c048-0423-4d6e-b86b-4e9752515333.xlsx` | XLSX | data | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./data/db/evalvault_run_d05a984a-9a3a-4f5e-ba14-53df740e8ff2.xlsx` | XLSX | data | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./data/db/evalvault_run_d0b2dc79-cbb7-4240-b167-f8f048d33988.xlsx` | XLSX | data | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./data/db/evalvault_run_d1101a80-a6c5-429e-9ba0-4c9016df9157.xlsx` | XLSX | data | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./data/db/evalvault_run_d1745d63-5e65-4f24-9ddc-45d342a63332.xlsx` | XLSX | data | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./data/db/evalvault_run_d17be6d0-a2d9-471a-84ba-11b8f710730c.xlsx` | XLSX | data | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./data/db/evalvault_run_d1ac41b0-609d-4f7a-b760-10ab6111def9.xlsx` | XLSX | data | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./data/db/evalvault_run_d37b328b-605e-4efd-98f4-4e91e9e749c7.xlsx` | XLSX | data | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./data/db/evalvault_run_d603bc7e-fbe0-4a13-a257-66a791f4bf21.xlsx` | XLSX | data | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./data/db/evalvault_run_d6472edd-9e07-4b73-9baf-addc0fb2717d.xlsx` | XLSX | data | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./data/db/evalvault_run_d648258a-443e-47b1-b8bb-1c90807ea531.xlsx` | XLSX | data | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./data/db/evalvault_run_d682114e-45f2-4427-8dff-2739574ce733.xlsx` | XLSX | data | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./data/db/evalvault_run_d6f5ef41-70dd-4e77-9b95-6738d5c964bd.xlsx` | XLSX | data | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./data/db/evalvault_run_d701e72c-4eb4-4656-8809-999b468883e2.xlsx` | XLSX | data | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./data/db/evalvault_run_d7c25cf2-dc61-4974-aaff-ccd14e3823a6.xlsx` | XLSX | data | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./data/db/evalvault_run_d7e30a5f-d093-4802-ab6e-414454c6db0a.xlsx` | XLSX | data | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./data/db/evalvault_run_d9113f70-ee04-4b6c-939e-a0dcbf64a890.xlsx` | XLSX | data | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./data/db/evalvault_run_d988eadd-ed89-441c-bacd-a5dfbbbaddc2.xlsx` | XLSX | data | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./data/db/evalvault_run_db9fb87e-46e4-4024-b37b-1a33816023df.xlsx` | XLSX | data | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./data/db/evalvault_run_dc5de642-6b34-4163-a114-4cb483323ddc.xlsx` | XLSX | data | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./data/db/evalvault_run_dd6fac8b-e9ca-439c-9127-06a9e8e07824.xlsx` | XLSX | data | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./data/db/evalvault_run_de5a64e4-9985-4780-9105-2a0fc30cee4b.xlsx` | XLSX | data | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./data/db/evalvault_run_dfa68917-b6da-41f1-bf05-d54104348f09.xlsx` | XLSX | data | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./data/db/evalvault_run_e1e634c7-47ea-419b-9a2f-b41509b5864e.xlsx` | XLSX | data | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./data/db/evalvault_run_e28c3a3b-be85-4302-b65f-4615a98725c5.xlsx` | XLSX | data | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./data/db/evalvault_run_e4155a28-4cab-4dfe-a2bd-2e0df2d67560.xlsx` | XLSX | data | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./data/db/evalvault_run_e44ce70e-6621-43f9-8463-2b3979188a76.xlsx` | XLSX | data | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./data/db/evalvault_run_e54cf74b-3091-4cf3-a69c-d667e4fc38a4.xlsx` | XLSX | data | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./data/db/evalvault_run_e5c97788-33b0-4c1d-9a81-cf156598437c.xlsx` | XLSX | data | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./data/db/evalvault_run_e60eebd7-b2c4-40d1-8980-b8bb59170875.xlsx` | XLSX | data | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./data/db/evalvault_run_e7bceaca-6aee-4df5-879f-47d774790e3d.xlsx` | XLSX | data | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./data/db/evalvault_run_e7e37328-8a80-4572-8a5a-43d46b9a885b.xlsx` | XLSX | data | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./data/db/evalvault_run_e84c44b9-1e8b-4f2e-a8db-c6ae6b598ddb.xlsx` | XLSX | data | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./data/db/evalvault_run_e870a6a7-682a-48ac-b09e-b2660dec21c7.xlsx` | XLSX | data | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./data/db/evalvault_run_e8fe34ca-2928-4fe6-a14a-8383fb4f0e53.xlsx` | XLSX | data | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./data/db/evalvault_run_e91fc5d5-4e64-4fbf-84d2-31a3e82b425f.xlsx` | XLSX | data | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./data/db/evalvault_run_ead3872f-666d-48ab-9e27-78a0be842490.xlsx` | XLSX | data | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./data/db/evalvault_run_eaeefde9-78a4-4f46-b746-2e98617f9338.xlsx` | XLSX | data | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./data/db/evalvault_run_eb30c763-a03f-4153-bb21-b945ce055899.xlsx` | XLSX | data | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./data/db/evalvault_run_ecf16af6-0191-4e31-8806-a2b63bc097b2.xlsx` | XLSX | data | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./data/db/evalvault_run_ed709b2e-150f-4c56-8f21-86c0831d0252.xlsx` | XLSX | data | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./data/db/evalvault_run_ed994516-07cb-4a52-a0d7-42648fe804ee.xlsx` | XLSX | data | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./data/db/evalvault_run_ee009863-a987-4958-b62c-1c492427eb68.xlsx` | XLSX | data | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./data/db/evalvault_run_ef05b249-2d1c-4bc3-91e7-ccf2e78aef3e.xlsx` | XLSX | data | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./data/db/evalvault_run_efed980d-6b33-4bab-859a-bda1a637a08e.xlsx` | XLSX | data | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./data/db/evalvault_run_f05b4376-0117-4373-8ac9-5105c846f53b.xlsx` | XLSX | data | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./data/db/evalvault_run_f411f3cc-cf92-4886-9d80-f572670bd2a2.xlsx` | XLSX | data | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./data/db/evalvault_run_f4aee7b9-bfee-41c8-871b-9ddc29e72551.xlsx` | XLSX | data | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./data/db/evalvault_run_f50b8779-1b67-42bd-a8f2-92efbc3bf61b.xlsx` | XLSX | data | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./data/db/evalvault_run_f58ca51a-9429-4eed-8b2f-6cb4ec1f7f5b.xlsx` | XLSX | data | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./data/db/evalvault_run_f58e999c-53f9-464a-a670-7cec0fa101a2.xlsx` | XLSX | data | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./data/db/evalvault_run_f673ef01-4ce6-4ae9-996e-26bb9aa93a63.xlsx` | XLSX | data | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./data/db/evalvault_run_f744a821-f57e-4ce3-8d9b-c3d4e1fec35c.xlsx` | XLSX | data | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./data/db/evalvault_run_f7a6c976-ef1c-4e38-affe-78a4755382d2.xlsx` | XLSX | data | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./data/db/evalvault_run_f84f2539-753d-40ad-80ac-d5ce51f4dd2e.xlsx` | XLSX | data | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./data/db/evalvault_run_f8c3d298-32f7-4d80-8947-259c49c69390.xlsx` | XLSX | data | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./data/db/evalvault_run_f8d3b612-4045-4794-ba87-30aaf3653432.xlsx` | XLSX | data | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./data/db/evalvault_run_f900c4c6-b4e7-4d02-aaff-ec9db737796d.xlsx` | XLSX | data | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./data/db/evalvault_run_f968f32f-ff8f-43f4-84ee-132a05de3ade.xlsx` | XLSX | data | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./data/db/evalvault_run_f9cca87d-ad43-41f2-b562-4718ad402d5a.xlsx` | XLSX | data | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./data/db/evalvault_run_fa5f01e9-5b2f-428b-8ddc-c7dfff2f8492.xlsx` | XLSX | data | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./data/db/evalvault_run_fa6068c9-26b2-4489-81ea-31b49b72007b.xlsx` | XLSX | data | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./data/db/evalvault_run_fa8bf4b9-181c-4147-ad19-d738df77c585.xlsx` | XLSX | data | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./data/db/evalvault_run_fb1f6ca2-9e23-4f5f-911d-0e76bd97d831.xlsx` | XLSX | data | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./data/db/evalvault_run_fb68e29f-261d-4dee-9e11-85fe44c9a3a8.xlsx` | XLSX | data | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./data/db/evalvault_run_fbf23fe1-7c33-4113-9404-12732fe3ccd3.xlsx` | XLSX | data | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./data/db/evalvault_run_fcf25836-d83d-4e54-b7b2-fabae359dc84.xlsx` | XLSX | data | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./data/db/evalvault_run_fd267590-cbb6-4841-8811-fca669a1eaca.xlsx` | XLSX | data | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./data/db/evalvault_run_fe576c72-6a58-4bbf-b6e6-58a229978eab.xlsx` | XLSX | data | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./data/db/evalvault_run_fec0c8cd-00a0-49c8-bb96-695b712455c5.xlsx` | XLSX | data | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./data/db/evalvault_run_fec3631a-c091-4326-9e1b-52cfe4bf4386.xlsx` | XLSX | data | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./data/db/evalvault_run_feebe396-1d73-44e2-8f0d-08fb3a080d30.xlsx` | XLSX | data | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./data/db/evalvault_run_ff39e1de-e15b-419d-a471-04be10dd8bab.xlsx` | XLSX | data | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./data/e2e_results/e2e_evaluations.db` | DB | data | lens:데이터·ML;type:데이터 | 포함 | - | 2026-01-28T17:51:27 | binary-scan | size: 1363968 bytes | DB binary file (1363968 bytes) | 내부 |
| `./data/e2e_results/summary_eval_minimal_custom.json` | JSON | data | lens:데이터·ML;type:데이터 | 포함 | - | 2026-01-28T17:51:27 | read-full | last: } | JSON file: keys: run_id,dataset_name,dataset_version,model_name,started_at,finished_at,total_test_cases,passed_test_cases | 내부 |
| `./data/e2e_results/summary_eval_minimal_custom.xlsx` | XLSX | data | lens:데이터·ML;type:데이터 | 포함 | - | 2026-01-28T17:51:27 | binary-scan | size: 19457 bytes | XLSX binary file (19457 bytes) | 내부 |
| `./data/e2e_results/summary_eval_minimal_probe.json` | JSON | data | lens:데이터·ML;type:데이터 | 포함 | - | 2026-01-28T17:51:27 | read-full | last: } | JSON file: keys: run_id,dataset_name,dataset_version,model_name,started_at,finished_at,total_test_cases,passed_test_cases | 내부 |
| `./data/e2e_results/summary_eval_single_case.json` | JSON | data | lens:데이터·ML;type:데이터 | 포함 | - | 2026-01-28T17:51:27 | read-full | last: } | JSON file: keys: name,version,thresholds,test_cases | 내부 |
| `./data/e2e_results/summary_eval_single_case.xlsx` | XLSX | data | lens:데이터·ML;type:데이터 | 포함 | - | 2026-01-28T17:51:27 | binary-scan | size: 17210 bytes | XLSX binary file (17210 bytes) | 내부 |
| `./data/e2e_results/summary_eval_single_case_prompt.json` | JSON | data | lens:데이터·ML;type:데이터 | 포함 | - | 2026-01-28T17:51:27 | read-full | last: } | JSON file: keys: run_id,dataset_name,dataset_version,model_name,started_at,finished_at,total_test_cases,passed_test_cases | 내부 |
| `./data/evaluations.db` | DB | data | lens:데이터·ML;type:데이터 | 포함 | - | 2026-01-28T17:51:27 | binary-scan | size: 69632 bytes | DB binary file (69632 bytes) | 내부 |
| `./data/evalvault.db` | DB | data | lens:데이터·ML;type:데이터 | 포함 | - | 2026-01-28T17:51:27 | binary-scan | size: 303104 bytes | DB binary file (303104 bytes) | 내부 |
| `./data/kg/knowledge_graph.json` | JSON | data | lens:데이터·ML;type:데이터 | 포함 | - | 2026-01-28T17:51:27 | read-full | last: } | JSON file: keys: type,stats,graph | 내부 |
| `./data/rag/user_guide_bm25.json` | JSON | data | lens:데이터·ML;type:데이터 | 포함 | - | 2026-01-28T17:51:27 | read-full | last: } | JSON file: keys: version,source,source_hash,chunk_limit,created_at,documents,tokens | 내부 |
| `./data/raw/The Complete Guide to Mastering Suno Advanced Strategies for Professional Music Generation.md` | Markdown | data | lens:데이터·ML;type:데이터 | 포함 | - | 2026-01-28T17:51:27 | read-full | last: * \[Sidechaining\] - Rhythmic volume ducking triggered by another signal | Markdown file: The Complete Guide to Mastering Suno: Advanced Strategies for Professional Music Generation | 내부 |
| `./data/raw/doc.txt` | Text | data | lens:데이터·ML;type:데이터 | 포함 | - | 2026-01-28T17:51:27 | read-full | last: hello | Text file: doc.txt | 내부 |
| `./data/raw/edge_cases.json` | JSON | data | lens:데이터·ML;type:데이터 | 포함 | - | 2026-01-28T17:51:27 | read-full | last: } | JSON file: keys: name,version,description,test_cases | 내부 |
| `./data/raw/run_mode_full_domain_memory.json` | JSON | data | lens:데이터·ML;type:데이터 | 포함 | - | 2026-01-28T17:51:27 | read-full | last: } | JSON file: keys: name,version,description,metadata,thresholds,test_cases | 내부 |
| `./data/raw/sample_rag_knowledge.txt` | Text | data | lens:데이터·ML;type:데이터 | 포함 | - | 2026-01-28T17:51:27 | read-full | last: Domain Memory in EvalVault allows the system to learn from past evaluations to improve future performance. | Text file: sample_rag_knowledge.txt | 내부 |
| `./dataset_templates/dataset_template.csv` | CSV | misc | lens:제품;type:소스 | 포함 | - | 2026-01-28T17:51:27 | read-full | last: id,question,answer,contexts,ground_truth,threshold_faithfulness,threshold_answer_relevancy,threshold_context_precision,t | CSV file: dataset_template.csv | 내부 |
| `./dataset_templates/dataset_template.json` | JSON | misc | lens:제품;type:소스 | 포함 | - | 2026-01-28T17:51:27 | read-full | last: } | JSON file: keys: name,version,description,thresholds,metadata,test_cases | 내부 |
| `./dataset_templates/dataset_template.xlsx` | XLSX | misc | lens:제품;type:소스 | 포함 | - | 2026-01-28T17:51:27 | binary-scan | size: 4962 bytes | XLSX binary file (4962 bytes) | 내부 |
| `./dataset_templates/method_input_template.json` | JSON | misc | lens:제품;type:소스 | 포함 | - | 2026-01-28T17:51:27 | read-full | last: } | JSON file: keys: name,version,metadata,thresholds,test_cases | 내부 |
| `./docker-compose.langfuse.yml` | YAML | infra | lens:운영;type:설정 | 포함 | - | 2026-01-28T17:51:27 | read-full | last:     driver: local | YAML file: docker-compose.langfuse.yml | 내부 |
| `./docker-compose.offline.yml` | YAML | misc | lens:제품;type:소스 | 포함 | - | 2026-01-28T17:51:27 | read-full | last:     driver: bridge | YAML file: docker-compose.offline.yml | 내부 |
| `./docker-compose.phoenix.yaml` | YAML | infra | lens:운영;type:설정 | 포함 | - | 2026-01-28T17:51:27 | read-full | last:   phoenix_data: | YAML file: docker-compose.phoenix.yaml | 내부 |
| `./docker-compose.yml` | YAML | infra | lens:운영;type:설정 | 포함 | - | 2026-01-28T17:51:27 | read-full | last:     driver: local | YAML file: docker-compose.yml | 내부 |
| `./docs/INDEX.md` | Markdown | docs | lens:제품;type:문서 | 포함 | - | 2026-01-28T17:51:27 | read-full | last: - 큰 변경(설계/운영/보안/품질 기준)은 `new_whitepaper/`에 먼저 반영하고, 필요한 부분만 `guides/`로 노출합니다. | Markdown file: EvalVault 문서 인덱스 | 내부 |
| `./docs/README.ko.md` | Markdown | docs | lens:제품;type:문서 | 포함 | - | 2026-01-28T17:51:27 | read-full | last: EvalVault는 \[Apache 2.0\](https://github.com/ntts9990/EvalVault/blob/main/LICENSE.md) 라이선스를 따릅니다. | Markdown file: EvalVault (한국어) | 내부 |
| `./docs/ROADMAP.md` | Markdown | docs | lens:제품;type:문서 | 포함 | - | 2026-01-28T17:51:27 | read-full | last: - 설계/운영 원칙과 변경 시 업데이트 가이드는 `new_whitepaper/INDEX.md` 및 각 챕터의 "향후 변경 시 업데이트 가이드"를 기준으로 동기화합니다. | Markdown file: EvalVault 로드맵 (Roadmap) | 내부 |
| `./docs/STATUS.md` | Markdown | docs | lens:제품;type:문서 | 포함 | - | 2026-01-28T17:51:27 | read-full | last: - 트레이싱 표준: `architecture/open-rag-trace-spec.md` | Markdown file: EvalVault 상태 요약 (Status) | 내부 |
| `./docs/api/adapters/inbound.md` | Markdown | docs | lens:제품;type:문서 | 포함 | - | 2026-01-28T17:51:27 | read-full | last: For detailed CLI usage, see the \[User Guide\](../guides/USER_GUIDE.md). | Markdown file: Inbound Adapters | 내부 |
| `./docs/api/adapters/outbound.md` | Markdown | docs | lens:제품;type:문서 | 포함 | - | 2026-01-28T17:51:27 | read-full | last: ``` | Markdown file: Outbound Adapters | 내부 |
| `./docs/api/config.md` | Markdown | docs | lens:제품;type:문서 | 포함 | - | 2026-01-28T17:51:27 | read-full | last: Invalid configuration will raise a clear error message at startup. | Markdown file: Configuration | 내부 |
| `./docs/api/domain/entities.md` | Markdown | docs | lens:제품;type:문서 | 포함 | - | 2026-01-28T17:51:27 | read-full | last:       show_root_heading: false | Markdown file: Domain Entities | 내부 |
| `./docs/api/domain/metrics.md` | Markdown | docs | lens:제품;type:문서 | 포함 | - | 2026-01-28T17:51:27 | read-full | last: For detailed metric descriptions, see the \[User Guide\](../guides/USER_GUIDE.md#metrics). | Markdown file: Custom Metrics | 내부 |
| `./docs/api/domain/services.md` | Markdown | docs | lens:제품;type:문서 | 포함 | - | 2026-01-28T17:51:27 | read-full | last:       show_source: true | Markdown file: Domain Services | 내부 |
| `./docs/api/ports/inbound.md` | Markdown | docs | lens:제품;type:문서 | 포함 | - | 2026-01-28T17:51:27 | read-full | last: - **Isolation**: Domain logic independent of external dependencies | Markdown file: Inbound Ports | 내부 |
| `./docs/api/ports/outbound.md` | Markdown | docs | lens:제품;type:문서 | 포함 | - | 2026-01-28T17:51:27 | read-full | last: See the \[Developer Whitepaper\](../new_whitepaper/02_architecture.md) for details on boundaries/ports/adapters when im | Markdown file: Outbound Ports | 내부 |
| `./docs/architecture/open-rag-trace-collector.md` | Markdown | docs | lens:제품;type:문서 | 포함 | - | 2026-01-28T17:51:27 | read-full | last: - 2026-01-10: Draft v0.1 최초 작성 | Markdown file: Open RAG Trace Collector 구성 (Draft) | 내부 |
| `./docs/architecture/open-rag-trace-spec.md` | Markdown | docs | lens:제품;type:문서 | 포함 | - | 2026-01-28T17:51:27 | read-full | last: - 2026-01-10: Draft v0.1 최초 작성 | Markdown file: Open RAG Trace Spec (Draft) | 내부 |
| `./docs/getting-started/INSTALLATION.md` | Markdown | docs | lens:제품;type:문서 | 포함 | - | 2026-01-28T17:51:27 | read-full | last: - 프로젝트 개요(영문): \[README.en.md\](../../README.en.md) | Markdown file: EvalVault 설치 가이드 | 내부 |
| `./docs/guides/AGENTS_SYSTEM_GUIDE.md` | Markdown | docs | lens:제품;type:문서 | 포함 | - | 2026-01-28T17:51:27 | read-full | last: 	5.	Liang, G., & Tong, Q. (2025). LLM-Powered AI Agent Systems and Their Applications in Industry. Proceedings of IEEE I | Markdown file: AGENTS_SYSTEM_GUIDE.md | 내부 |
| `./docs/guides/CHAINLIT_INTEGRATION_PLAN.md` | Markdown | docs | lens:제품;type:문서 | 포함 | - | 2026-01-28T17:51:27 | read-full | last: - 이후 MCP 서버 구현 여부 결정 | Markdown file: Chainlit 통합 계획 (MCP 포함) | 내부 |
| `./docs/guides/CI_REGRESSION_GATE.md` | Markdown | docs | lens:제품;type:문서 | 포함 | - | 2026-01-28T17:51:27 | read-full | last: - `3`: 런 조회 실패/데이터 누락 등 **복구 불가능한 오류** | Markdown file: CI 회귀 게이트 (Regression Gate) | 내부 |
| `./docs/guides/CLI_MCP_PLAN.md` | Markdown | docs | lens:제품;type:문서 | 포함 | - | 2026-01-28T17:51:27 | read-full | last: > 이 문서는 진행 상황에 따라 지속 업데이트합니다. | Markdown file: EvalVault CLI → MCP 이식 계획 (Living Document) | 내부 |
| `./docs/guides/CLI_PARALLEL_FEATURES_SPEC.md` | Markdown | docs | lens:제품;type:문서 | 포함 | - | 2026-01-28T17:51:27 | read-full | last: - Async batch executor: `domain/services/async_batch_executor.py` | Markdown file: CLI Parallel Features Spec (Draft) | 내부 |
| `./docs/guides/CLI_UX_REDESIGN.md` | Markdown | docs | lens:제품;type:문서 | 포함 | - | 2026-01-28T17:51:27 | read-full | last:   1차 적용에서는 alias와 문서 정리로 혼선을 줄인다. | Markdown file: CLI UX 개선 설계서 (비파괴적 개선) | 내부 |
| `./docs/guides/DEV_GUIDE.md` | Markdown | docs | lens:제품;type:문서 | 포함 | - | 2026-01-28T17:51:27 | read-full | last: - 실행 결과 엑셀 컬럼 설명: `docs/guides/EVALVAULT_RUN_EXCEL_SHEETS.md` | Markdown file: EvalVault 개발 가이드 (Dev Guide) | 내부 |
| `./docs/guides/DOCS_REFRESH_PLAN.md` | Markdown | docs | lens:제품;type:문서 | 포함 | - | 2026-01-28T17:51:27 | read-full | last: - 이 계획에 따라 실제 문서 정리 작업을 진행합니다. | Markdown file: 문서 최신화/정리 작업 계획 | 내부 |
| `./docs/guides/EVALVAULT_DIAGNOSTIC_PLAYBOOK.md` | Markdown | docs | lens:제품;type:문서 | 포함 | - | 2026-01-28T17:51:27 | read-full | last: > 스테이지/디버그 진단은 Intent 분류 없이 `evalvault stage`, `evalvault debug report`로 실행한다. | Markdown file: EvalVault 진단 플레이북 (Diagnostic Playbook) | 내부 |
| `./docs/guides/EVALVAULT_RUN_EXCEL_SHEETS.md` | Markdown | docs | lens:제품;type:문서 | 포함 | - | 2026-01-28T17:51:27 | read-full | last: - 샘플: `metric_name=faithfulness`, `score=0.82` | Markdown file: EvalVault Run 엑셀 시트/컬럼 요약 | 내부 |
| `./docs/guides/EVALVAULT_WORK_PLAN.md` | Markdown | docs | lens:제품;type:문서 | 포함 | - | 2026-01-28T17:51:27 | read-full | last: - 재확인 필요: 동일 에러 재발 여부 | Markdown file: EvalVault 작업 계획서 (Archived) | 내부 |
| `./docs/guides/EXTERNAL_TRACE_API_SPEC.md` | Markdown | docs | lens:제품;type:문서 | 포함 | - | 2026-01-28T17:51:27 | read-full | last: - **비정형 로그(Stage Event)**는 `stage ingest` → `stage summary` → 분석 모듈로 전환 | Markdown file: 외부 로그 연동 API 규격 (OpenTelemetry + OpenInference) | 내부 |
| `./docs/guides/Extension_2.md` | Markdown | docs | lens:제품;type:문서 | 포함 | - | 2026-01-28T17:51:27 | read-full | last: - LLM judge bias: https://llm-judge-bias.github.io/ | Markdown file: RAG 시스템 데이터 난이도 평가 및 평가용 LLM 파인튜닝 전략 (현실적 관점) | 내부 |
| `./docs/guides/Extension_Data_Difficulty_Profiling_Custom_Judge_Model.md` | Markdown | docs | lens:제품;type:문서 | 포함 | - | 2026-01-28T17:51:27 | read-full | last: 추가 논의가 필요한 부분이 있으면 말씀해 주세요. | Markdown file: EvalVault 확장 제안서: 데이터 난이도 프로파일링 + 평가 전문 LLM 구축 | 내부 |
| `./docs/guides/INSURANCE_SUMMARY_METRICS_PLAN.md` | Markdown | docs | lens:제품;type:문서 | 포함 | - | 2026-01-28T17:51:27 | read-full | last: 3) Web UI | Markdown file: 보험 도메인 요약(Summary) 메트릭 확장 PRD/SDD (EvalVault) | 내부 |
| `./docs/guides/LENA_MVP_IMPLEMENTATION_PLAN.md` | Markdown | docs | lens:제품;type:문서 | 포함 | - | 2026-01-28T17:51:27 | read-full | last: - `K <= 1`일 때는 pred_var/mean_k 관련 필드를 제한하거나 warnings를 포함한다. | Markdown file: LENA MVP 구현 계획서 (EvalVault) | 내부 |
| `./docs/guides/LENA_RAGAS_CALIBRATION_DEV_PLAN.md` | Markdown | docs | lens:제품;type:문서 | 포함 | - | 2026-01-28T17:51:27 | read-full | last: - `docs/guides/PRD_LENA.md` | Markdown file: LENA + RAGAS 인간 피드백 보정 통합 개발 계획서 (개발 실행안) | 내부 |
| `./docs/guides/MULTITURN_EVAL_GUIDE.md` | Markdown | docs | lens:제품;type:문서 | 포함 | - | 2026-01-28T17:51:27 | read-full | last: - `docs/templates/ragas_dataset_example_ko90_en10.json` | Markdown file: 멀티턴 평가 가이드 | 내부 |
| `./docs/guides/NEXT_STEPS_EXECUTION_PLAN.md` | Markdown | docs | lens:제품;type:문서 | 포함 | - | 2026-01-28T17:51:27 | read-full | last: - 작업 완료 시 `.sisyphus/notepads/*/worklog.md`에 기록 | Markdown file: 다음 개발 실행 계획 (P0→P3) | 내부 |
| `./docs/guides/OFFLINE_DOCKER.md` | Markdown | docs | lens:제품;type:문서 | 포함 | - | 2026-01-28T17:51:27 | read-full | last: - Docker compose pull: https://docs.docker.com/reference/cli/docker/compose/pull/ | Markdown file: 폐쇄망(에어갭) Docker 배포 가이드 | 내부 |
| `./docs/guides/OPEN_RAG_TRACE_INTERNAL_ADAPTER.md` | Markdown | docs | lens:제품;type:문서 | 포함 | - | 2026-01-28T17:51:27 | read-full | last: - 2026-01-10: Draft v0.1 최초 작성 | Markdown file: Open RAG Trace 내부 시스템 최소 계측 래퍼 | 내부 |
| `./docs/guides/OPEN_RAG_TRACE_SAMPLES.md` | Markdown | docs | lens:제품;type:문서 | 포함 | - | 2026-01-28T17:51:27 | read-full | last: - 2026-01-10: Draft v0.1 최초 작성 | Markdown file: Open RAG Trace 최소 계측 샘플 | 내부 |
| `./docs/guides/P0_P3_EXECUTION_REPORT.md` | Markdown | docs | lens:제품;type:문서 | 포함 | - | 2026-01-28T17:51:27 | read-full | last: - 프론트 빌드 경고(번들 크기) 존재하나 기존 경고와 동일 | Markdown file: P0-P3 작업 보고서 | 내부 |
| `./docs/guides/P1_P4_WORK_PLAN.md` | Markdown | docs | lens:제품;type:문서 | 포함 | - | 2026-01-28T17:51:27 | read-full | last: *본 계획서는 feature_verification_report.md의 Gap 분석 결과를 기반으로 작성되었습니다.* | Markdown file: P1-P4 작업 계획서 | 내부 |
| `./docs/guides/PARALLEL_WORK_APPROVAL_RULES.md` | Markdown | docs | lens:제품;type:문서 | 포함 | - | 2026-01-28T17:51:27 | read-full | last: ``` | Markdown file: 병렬 작업 승인 체계 (공유 스키마/공유 파일) | 내부 |
| `./docs/guides/PRD_LENA.md` | Markdown | docs | lens:제품;type:문서 | 포함 | - | 2026-01-28T17:51:27 | read-full | last: ⸻ | Markdown file: A/B 비교 | 내부 |
| `./docs/guides/PROJECT_STATUS_AND_PLAN.md` | Markdown | docs | lens:제품;type:문서 | 포함 | - | 2026-01-28T17:51:27 | read-full | last: - `docs/guides/RAG_PERFORMANCE_IMPLEMENTATION_LOG.md` | Markdown file: EvalVault 개발 상태/실행 계획 (Archived) | 내부 |
| `./docs/guides/RAGAS_HUMAN_FEEDBACK_CALIBRATION_GUIDE.md` | Markdown | docs | lens:제품;type:문서 | 포함 | - | 2026-01-28T17:51:27 | read-full | last: - 2026-01-13 v0.1: 두 문서 통합 초안 작성 | Markdown file: RAGAS 평가를 인간 피드백으로 보정하는 방법론 | 내부 |
| `./docs/guides/RAG_CLI_WORKFLOW_TEMPLATES.md` | Markdown | docs | lens:제품;type:문서 | 포함 | - | 2026-01-28T17:51:27 | read-full | last: - 프롬프트 추천 설계: `docs/guides/prompt_suggestions_design.md` | Markdown file: EvalVault CLI 시나리오 워크플로 가이드 | 내부 |
| `./docs/guides/RAG_NOISE_REDUCTION_GUIDE.md` | Markdown | docs | lens:제품;type:문서 | 포함 | - | 2026-01-28T17:51:27 | read-full | last: - 시스템 개요: `docs/new_whitepaper/01_overview.md` | Markdown file: RAG 평가 노이즈 저감 정리서 | 내부 |
| `./docs/guides/RAG_PERFORMANCE_IMPLEMENTATION_LOG.md` | Markdown | docs | lens:제품;type:문서 | 포함 | - | 2026-01-28T17:51:27 | read-full | last:   - 테스트: 문서 변경(실행 테스트 없음) | Markdown file: RAG Performance Improvement Execution Log | 내부 |
| `./docs/guides/RAG_PERFORMANCE_IMPROVEMENT_PROPOSAL.md` | Markdown | docs | lens:제품;type:문서 | 포함 | - | 2026-01-28T17:51:27 | read-full | last: - \[R26\] https://www.frontiersin.org/journals/public-health/articles/10.3389/fpubh.2025.1635381/full | Markdown file: EvalVault 목적/미션 정의 및 RAG 성능 분석·개선 제안서 | 내부 |
| `./docs/guides/RELEASE_CHECKLIST.md` | Markdown | docs | lens:제품;type:문서 | 포함 | - | 2026-01-28T17:51:27 | read-full | last: - 사용자/내부 피드백 수집 및 이슈 기록 | Markdown file: 배포 체크리스트 & 릴리즈 노트 템플릿 | 내부 |
| `./docs/guides/USER_GUIDE.md` | Markdown | docs | lens:제품;type:문서 | 포함 | - | 2026-01-28T17:51:27 | read-full | last: 필요 시 `uv run evalvault --help`로 명령 전체 목록을 확인하세요. | Markdown file: EvalVault 사용자 가이드 | 내부 |
| `./docs/guides/WEBUI_CLI_ROLLOUT_PLAN.md` | Markdown | docs | lens:제품;type:문서 | 포함 | - | 2026-01-28T17:51:27 | read-full | last: - 초보 사용자 워크플로 시나리오 테스트. | Markdown file: Web UI 확장 설계서 (CLI 전 기능 반영) | 내부 |
| `./docs/guides/WORKLOG_LAST_2_DAYS.md` | Markdown | docs | lens:제품;type:문서 | 포함 | - | 2026-01-28T17:51:27 | read-full | last: 3. Domain Memory Phase 2 구현 범위 합의 | Markdown file: 최근 2일 작업 정리 및 개발 실행 로그 | 내부 |
| `./docs/guides/cli_process.md` | Markdown | docs | lens:제품;type:문서 | 포함 | - | 2026-01-28T17:51:27 | read-full | last: - 이유: 시나리오 기반 실행 템플릿과 운영 팁을 하나로 합쳐, 사용자가 원하는 작동 방식을 더 쉽게 찾을 수 있도록 재구성했습니다. | Markdown file: EvalVault CLI 실행 프로세스 | 내부 |
| `./docs/guides/prompt_suggestions_design.md` | Markdown | docs | lens:제품;type:문서 | 포함 | - | 2026-01-28T17:51:27 | read-full | last: 5. A가 CLI 요약 출력 | Markdown file: 프롬프트 후보 평가·추천(옵션 C) 설계 문서 | 내부 |
| `./docs/guides/rag_human_feedback_calibration_implementation_plan.md` | Markdown | docs | lens:제품;type:문서 | 포함 | - | 2026-01-28T17:51:27 | read-full | last: - `src/evalvault/adapters/outbound/analysis/nlp_adapter.py` | Markdown file: RAG 인간 피드백 보정: 상세 구현 계획서 | 내부 |
| `./docs/guides/refactoring_strategy.md` | Markdown | docs | lens:제품;type:문서 | 포함 | - | 2026-01-28T17:51:27 | read-full | last: ``` | Markdown file: **Problem 1-Pager (복잡한 작업 전 필수)** | 내부 |
| `./docs/guides/repeat_query.md` | Markdown | docs | lens:제품;type:문서 | 포함 | - | 2026-01-28T17:51:27 | read-full | last: - 실패 분석: 반복 적용 후 `insight_generator`로 오류 유형 변화 확인 | Markdown file: 11. EvalVault 적용 범위 및 구현 계획(소스 기반) | 내부 |
| `./docs/handbook/appendix-file-inventory.md` | Markdown | docs | lens:제품;type:문서 | 포함 | - | 2026-01-28T17:51:27 | read-full | last: - 이 경로의 파일은 Raw List에는 포함되지만, 교과서 본편/부록의 상세 해설 대상에서는 제외로 표시합니다. | Markdown file: 파일 인벤토리 (File Inventory) | 내부 |
| `./docs/mapping/component-to-whitepaper.yaml` | YAML | docs | lens:제품;type:문서 | 포함 | - | 2026-01-28T17:51:27 | read-full | last:           subsection: 모델 프로필 | YAML file: component-to-whitepaper.yaml | 내부 |
| `./docs/new_whitepaper/00_frontmatter.md` | Markdown | docs | lens:제품;type:문서 | 포함 | - | 2026-01-28T17:51:27 | read-full | last: - `docs/STATUS.md` (1페이지 상태 요약) | Markdown file: EvalVault 개발 백서 | 내부 |
| `./docs/new_whitepaper/01_overview.md` | Markdown | docs | lens:제품;type:문서 | 포함 | - | 2026-01-28T17:51:27 | read-full | last: - \[ \] 문장이 과도하게 길거나, 모호한 추상 표현이 남발되지 않는가 | Markdown file: 01. 프로젝트 개요 | 내부 |
| `./docs/new_whitepaper/02_architecture.md` | Markdown | docs | lens:제품;type:문서 | 포함 | - | 2026-01-28T17:51:27 | read-full | last: - \[ \] 다이어그램 없이도 텍스트로 이해 가능한가 | Markdown file: 02. 아키텍처 설계 | 내부 |
| `./docs/new_whitepaper/03_data_flow.md` | Markdown | docs | lens:제품;type:문서 | 포함 | - | 2026-01-28T17:51:27 | read-full | last: - \[ \] 실패/예외 흐름이 최소한의 실무 힌트를 제공하는가 | Markdown file: 03. 데이터/실행 흐름 (run_id 중심) | 내부 |
| `./docs/new_whitepaper/04_components.md` | Markdown | docs | lens:제품;type:문서 | 포함 | - | 2026-01-28T17:51:27 | read-full | last: - \[ \] 경로가 실제로 존재하는가(문서가 코드와 싱크되는가) | Markdown file: 04. 주요 컴포넌트 지도 | 내부 |
| `./docs/new_whitepaper/05_expert_lenses.md` | Markdown | docs | lens:제품;type:문서 | 포함 | - | 2026-01-28T17:51:27 | read-full | last: - \[ \] ‘향후 변경 시’ 섹션이 실제로 리팩토링 대응에 도움이 되는가 | Markdown file: 05. 전문가 관점 통합 프레임 | 내부 |
| `./docs/new_whitepaper/06_implementation.md` | Markdown | docs | lens:제품;type:문서 | 포함 | - | 2026-01-28T17:51:27 | read-full | last: - \[ \] 단정적 서술로 코드와 문서가 어긋날 위험을 줄였는가 | Markdown file: 06. 구현 상세(어디를 보면 되는지) | 내부 |
| `./docs/new_whitepaper/07_advanced.md` | Markdown | docs | lens:제품;type:문서 | 포함 | - | 2026-01-28T17:51:27 | read-full | last:   을 근거로 이 장의 **4장**을 업데이트한다. | Markdown file: 07. 고급 기능 및 확장(Advanced) | 내부 |
| `./docs/new_whitepaper/08_customization.md` | Markdown | docs | lens:제품;type:문서 | 포함 | - | 2026-01-28T17:51:27 | read-full | last:   - 사용자용 SSoT(`docs/guides/USER_GUIDE.md`)와 충돌하지 않도록 링크를 추가한다. | Markdown file: 08. 커스터마이징(확장) 가이드 | 내부 |
| `./docs/new_whitepaper/09_quality.md` | Markdown | docs | lens:제품;type:문서 | 포함 | - | 2026-01-28T17:51:27 | read-full | last: - CI/릴리스 정책이 바뀌면, `AGENTS.md`와 함께 이 장의 **3장**을 갱신한다. | Markdown file: 09. 테스트/품질 보증(Quality) | 내부 |
| `./docs/new_whitepaper/10_performance.md` | Markdown | docs | lens:제품;type:문서 | 포함 | - | 2026-01-28T17:51:27 | read-full | last:     이 장의 **3.2**에 추가한다. | Markdown file: 10. 성능 최적화(Performance) | 내부 |
| `./docs/new_whitepaper/11_security.md` | Markdown | docs | lens:제품;type:문서 | 포함 | - | 2026-01-28T17:51:27 | read-full | last:   - 이 장의 **3.1** 목록을 업데이트한다. | Markdown file: 11. 보안/프라이버시(Security) | 내부 |
| `./docs/new_whitepaper/12_operations.md` | Markdown | docs | lens:제품;type:문서 | 포함 | - | 2026-01-28T17:51:27 | read-full | last:     이 장의 **4.2**를 업데이트한다. | Markdown file: 12. 운영/모니터링(Operations) | 내부 |
| `./docs/new_whitepaper/13_standards.md` | Markdown | docs | lens:제품;type:문서 | 포함 | - | 2026-01-28T17:51:27 | read-full | last:     이 장의 **3.2**를 업데이트하고, 기존 인덱스와의 호환성/마이그레이션 방침을 명시한다. | Markdown file: 13. 표준/생태계(Standards) | 내부 |
| `./docs/new_whitepaper/14_roadmap.md` | Markdown | docs | lens:제품;type:문서 | 포함 | - | 2026-01-28T17:51:27 | read-full | last:   - `docs/new_whitepaper/INDEX.md`와 함께 이 장의 **3장(업데이트 루틴)**을 갱신한다. | Markdown file: 14. 로드맵 및 향후 계획 | 내부 |
| `./docs/new_whitepaper/INDEX.md` | Markdown | docs | lens:제품;type:문서 | 포함 | - | 2026-01-28T17:51:27 | read-full | last: - 사용자 워크플로(명령/설정): `docs/guides/USER_GUIDE.md` | Markdown file: EvalVault 개발 백서 (new_whitepaper) | 내부 |
| `./docs/new_whitepaper/STYLE_GUIDE.md` | Markdown | docs | lens:제품;type:문서 | 포함 | - | 2026-01-28T17:51:27 | read-full | last:   - 아키텍처 경계(domain/ports/adapters) 이해 | Markdown file: EvalVault 개발 백서 (new_whitepaper) 작성 규칙 | 내부 |
| `./docs/refactor/REFAC_000_master_plan.md` | Markdown | docs | lens:제품;type:문서 | 포함 | - | 2026-01-28T17:51:27 | read-full | last: Every refactor step must be logged in `docs/refactor/logs/` using standard template. | Markdown file: Refactoring Master Plan (Structure-Only) | 내부 |
| `./docs/refactor/REFAC_010_agent_playbook.md` | Markdown | docs | lens:제품;type:문서 | 포함 | - | 2026-01-28T17:51:27 | read-full | last: Each agent must write a log before and after changes using the template in `REFAC_020_logging_policy.md`. | Markdown file: Agent Work Playbook (Parallel Execution) | 내부 |
| `./docs/refactor/REFAC_020_logging_policy.md` | Markdown | docs | lens:제품;type:문서 | 포함 | - | 2026-01-28T17:51:27 | read-full | last: - Request for explicit approval | Markdown file: Logging Policy and Templates | 내부 |
| `./docs/refactor/REFAC_030_phase0_responsibility_map.md` | Markdown | docs | lens:제품;type:문서 | 포함 | - | 2026-01-28T17:51:27 | read-full | last: - WBS prepared for Phase 1-3 | Markdown file: Phase 0 Responsibility Map | 내부 |
| `./docs/refactor/REFAC_040_wbs_parallel_plan.md` | Markdown | docs | lens:제품;type:문서 | 포함 | - | 2026-01-28T17:51:27 | read-full | last: - Explicit "behavior unchanged" confirmation | Markdown file: Work Breakdown Structure (WBS) and Parallel Plan | 내부 |
| `./docs/refactor/logs/phase-0-baseline.md` | Markdown | docs | lens:제품;type:문서 | 포함 | - | 2026-01-28T17:51:27 | read-full | last: - Follow-ups: | Markdown file: Refactor Log: Phase 0 - Baseline | 내부 |
| `./docs/refactor/logs/phase-1-evaluator.md` | Markdown | docs | lens:제품;type:문서 | 포함 | - | 2026-01-28T17:51:27 | read-full | last: - Follow-ups: | Markdown file: Refactor Log: Phase 1 - Evaluator | 내부 |
| `./docs/refactor/logs/phase-2-cli-run.md` | Markdown | docs | lens:제품;type:문서 | 포함 | - | 2026-01-28T17:51:27 | read-full | last: - Follow-ups: | Markdown file: Refactor Log: Phase 2 - CLI Run | 내부 |
| `./docs/refactor/logs/phase-3-analysis.md` | Markdown | docs | lens:제품;type:문서 | 포함 | - | 2026-01-28T17:51:27 | read-full | last: - Follow-ups: | Markdown file: Refactor Log: Phase 3 - Analysis | 내부 |
| `./docs/security_audit_worklog.md` | Markdown | docs | lens:제품;type:문서 | 포함 | - | 2026-01-28T17:51:27 | read-full | last: (추가 조사 및 보강 예정) | Markdown file: EvalVault 보안 전수조사 작업 기록 (중간) | 내부 |
| `./docs/stylesheets/extra.css` | CSS | docs | lens:제품;type:문서 | 포함 | - | 2026-01-28T17:51:27 | read-full | last: } | CSS file: extra.css | 내부 |
| `./docs/templates/dataset_template.csv` | CSV | docs | lens:제품;type:문서 | 포함 | - | 2026-01-28T17:51:27 | read-full | last: id,question,answer,contexts,ground_truth,threshold_faithfulness,threshold_answer_relevancy,threshold_context_precision,t | CSV file: dataset_template.csv | 내부 |
| `./docs/templates/dataset_template.json` | JSON | docs | lens:제품;type:문서 | 포함 | - | 2026-01-28T17:51:27 | read-full | last: } | JSON file: keys: name,version,description,thresholds,metadata,test_cases | 내부 |
| `./docs/templates/dataset_template.xlsx` | XLSX | docs | lens:제품;type:문서 | 포함 | - | 2026-01-28T17:51:27 | binary-scan | size: 4964 bytes | XLSX binary file (4964 bytes) | 내부 |
| `./docs/templates/eval_report_templates.md` | Markdown | docs | lens:제품;type:문서 | 포함 | - | 2026-01-28T17:51:27 | read-full | last: - action_3: | Markdown file: Eval Report Templates | 내부 |
| `./docs/templates/kg_template.json` | JSON | docs | lens:제품;type:문서 | 포함 | - | 2026-01-28T17:51:27 | read-full | last: } | JSON file: keys: entities,relations | 내부 |
| `./docs/templates/otel_openinference_trace_example.json` | JSON | docs | lens:제품;type:문서 | 포함 | - | 2026-01-28T17:51:27 | read-full | last: } | JSON file: keys: resourceSpans | 내부 |
| `./docs/templates/ragas_dataset_example_ko90_en10.json` | JSON | docs | lens:제품;type:문서 | 포함 | - | 2026-01-28T17:51:27 | read-full | last: } | JSON file: keys: name,version,thresholds,test_cases | 내부 |
| `./docs/templates/retriever_docs_template.json` | JSON | docs | lens:제품;type:문서 | 포함 | - | 2026-01-28T17:51:27 | read-full | last: } | JSON file: keys: documents | 내부 |
| `./docs/tools/generate-whitepaper.py` | Python | docs | lens:제품;type:문서 | 포함 | - | 2026-01-28T17:51:27 | read-full | last:     main() | Python file: generate-whitepaper.py | 내부 |
| `./docs/web_ui_analysis_migration_plan.md` | Markdown | docs | lens:제품;type:문서 | 포함 | - | 2026-01-28T17:51:27 | read-full | last: - 분석 실행 이력 저장/조회 범위 | Markdown file: Web UI 분석 기능 이관 계획 (SPSS/SAS 스타일) | 내부 |
| `./dummy_test_dataset.json` | JSON | misc | lens:제품;type:소스 | 포함 | - | 2026-01-28T17:51:27 | read-full | last: } | JSON file: keys: name,version,test_cases | 내부 |
| `./evalvault.db` | DB | misc | lens:제품;type:소스 | 포함 | - | 2026-01-28T17:51:27 | binary-scan | size: 1220608 bytes | DB binary file (1220608 bytes) | 내부 |
| `./evalvault_memory.db` | DB | misc | lens:제품;type:소스 | 포함 | - | 2026-01-28T17:51:27 | binary-scan | size: 237568 bytes | DB binary file (237568 bytes) | 내부 |
| `./examples/README.md` | Markdown | examples | lens:개발;type:소스 | 포함 | - | 2026-01-28T17:51:27 | read-full | last: - \[Developer Whitepaper\](../new_whitepaper/INDEX.md) - 설계/운영/품질 기준 | Markdown file: Examples | 내부 |
| `./examples/benchmarks/README.md` | Markdown | examples | lens:개발;type:소스 | 포함 | - | 2026-01-28T17:51:27 | read-full | last: **문서 끝** | Markdown file: Korean RAG Benchmark Guide | 내부 |
| `./examples/benchmarks/korean_rag/faithfulness_test.json` | JSON | examples | lens:개발;type:소스 | 포함 | - | 2026-01-28T17:51:27 | read-full | last: } | JSON file: keys: name,version,description,purpose,evaluation_metrics,test_categories,test_cases | 내부 |
| `./examples/benchmarks/korean_rag/insurance_qa_100.json` | JSON | examples | lens:개발;type:소스 | 포함 | - | 2026-01-28T17:51:27 | read-full | last: } | JSON file: keys: name,version,description,language,domain,metrics,test_cases | 내부 |
| `./examples/benchmarks/korean_rag/keyword_extraction_test.json` | JSON | examples | lens:개발;type:소스 | 포함 | - | 2026-01-28T17:51:27 | read-full | last: } | JSON file: keys: name,version,description,purpose,evaluation_metrics,methodology,test_cases,expected_results | 내부 |
| `./examples/benchmarks/korean_rag/retrieval_test.json` | JSON | examples | lens:개발;type:소스 | 포함 | - | 2026-01-28T17:51:27 | read-full | last: } | JSON file: keys: name,version,description,purpose,evaluation_metrics,test_categories,documents,test_cases | 내부 |
| `./examples/benchmarks/output/comparison.json` | JSON | examples | lens:개발;type:소스 | 포함 | - | 2026-01-28T17:51:27 | read-full | last: } | JSON file: keys: generated_at,comparisons | 내부 |
| `./examples/benchmarks/output/full_results.json` | JSON | examples | lens:개발;type:소스 | 포함 | - | 2026-01-28T17:51:27 | read-full | last: } | JSON file: keys: name,version,description,languages,domain,model_name,model_revision,summary | 내부 |
| `./examples/benchmarks/output/leaderboard.json` | JSON | examples | lens:개발;type:소스 | 포함 | - | 2026-01-28T17:51:27 | read-full | last: } | JSON file: keys: model,revision,average,pass_rate,korean-faithfulness-benchmark,korean-keyword-extraction-benchmark,korean-retrieval-benchma | 내부 |
| `./examples/benchmarks/output/results_mteb.json` | JSON | examples | lens:개발;type:소스 | 포함 | - | 2026-01-28T17:51:27 | read-full | last: } | JSON file: keys: name,version,description,languages,domain,model_name,model_revision,summary | 내부 |
| `./examples/benchmarks/output/retrieval_result.json` | JSON | examples | lens:개발;type:소스 | 포함 | - | 2026-01-28T17:51:27 | read-full | last: } | JSON file: keys: task_name,task_type,mteb_version,evalvault_version,dataset_revision,languages,scores,evaluation_time | 내부 |
| `./examples/benchmarks/run_korean_benchmark.py` | Python | examples | lens:개발;type:소스 | 포함 | - | 2026-01-28T17:51:27 | read-full | last:     sys.exit(main()) | Python file: run_korean_benchmark.py | 내부 |
| `./examples/kg_generator_demo.py` | Python | examples | lens:개발;type:소스 | 포함 | - | 2026-01-28T17:51:27 | read-full | last:     main() | Python file: Knowledge Graph Generator Demonstration. | 내부 |
| `./examples/method_plugin_template/README.md` | Markdown | examples | lens:개발;type:소스 | 포함 | - | 2026-01-28T17:51:27 | read-full | last: ``` | Markdown file: README.md | 내부 |
| `./examples/method_plugin_template/pyproject.toml` | TOML | examples | lens:개발;type:소스 | 포함 | - | 2026-01-28T17:51:27 | read-full | last: build-backend = "setuptools.build_meta" | TOML file: pyproject.toml | 내부 |
| `./examples/method_plugin_template/src/method_plugin_template/__init__.py` | Python | examples | lens:개발;type:소스 | 포함 | - | 2026-01-28T17:51:27 | read-full | last: """Template package for EvalVault method plugins.""" | Python file: Template package for EvalVault method plugins. | 내부 |
| `./examples/method_plugin_template/src/method_plugin_template/methods.py` | Python | examples | lens:개발;type:소스 | 포함 | - | 2026-01-28T17:51:27 | read-full | last:         return outputs | Python file: Example EvalVault method plugin implementation. | 내부 |
| `./examples/stage_events.jsonl` | JSONL | examples | lens:개발;type:소스 | 포함 | - | 2026-01-28T17:51:27 | binary-scan | size: 1159 bytes | JSONL binary file (1159 bytes) | 내부 |
| `./examples/usecase/comprehensive_workflow_test.py` | Python | examples | lens:개발;type:소스 | 포함 | - | 2026-01-28T17:51:27 | read-full | last:     asyncio.run(main()) | Python file: comprehensive_workflow_test.py | 내부 |
| `./examples/usecase/insurance_eval_dataset.json` | JSON | examples | lens:개발;type:소스 | 포함 | - | 2026-01-28T17:51:27 | read-full | last: } | JSON file: keys: name,version,description,domain,language,created_at,thresholds,test_cases | 내부 |
| `./examples/usecase/output/comprehensive_report.html` | HTML | examples | lens:개발;type:소스 | 포함 | - | 2026-01-28T17:51:27 | read-full | last: </html> | HTML file: comprehensive_report.html | 내부 |
| `./examples/usecase/output/evalvault_memory.db` | DB | examples | lens:개발;type:소스 | 포함 | - | 2026-01-28T17:51:27 | binary-scan | size: 503808 bytes | DB binary file (503808 bytes) | 내부 |
| `./frontend/.env.example` | EXAMPLE | misc | lens:제품;type:소스 | 포함 | - | 2026-01-28T17:54:02 | binary-scan | size: 190 bytes | EXAMPLE binary file (190 bytes) | 내부 |
| `./frontend/.gitignore` | File | misc | lens:제품;type:소스 | 포함 | - | 2026-01-28T17:54:02 | binary-scan | size: 286 bytes | File binary file (286 bytes) | 내부 |
| `./frontend/Dockerfile` | File | misc | lens:제품;type:소스 | 포함 | - | 2026-01-28T17:54:02 | binary-scan | size: 322 bytes | File binary file (322 bytes) | 내부 |
| `./frontend/README.md` | Markdown | misc | lens:제품;type:소스 | 포함 | - | 2026-01-28T17:54:02 | read-full | last: ``` | Markdown text file: React + TypeScript + Vite | 내부 |
| `./frontend/e2e/analysis-compare.spec.ts` | TypeScript | misc | lens:제품;type:소스 | 포함 | - | 2026-01-28T17:54:02 | read-full | last: }); | TypeScript text file: analysis-compare.spec.ts | 내부 |
| `./frontend/e2e/analysis-lab.spec.ts` | TypeScript | misc | lens:제품;type:소스 | 포함 | - | 2026-01-28T17:54:02 | read-full | last: }); | TypeScript text file: analysis-lab.spec.ts | 내부 |
| `./frontend/e2e/compare-runs.spec.ts` | TypeScript | misc | lens:제품;type:소스 | 포함 | - | 2026-01-28T17:54:02 | read-full | last: }); | TypeScript text file: compare-runs.spec.ts | 내부 |
| `./frontend/e2e/dashboard.spec.ts` | TypeScript | misc | lens:제품;type:소스 | 포함 | - | 2026-01-28T17:54:02 | read-full | last: }); | TypeScript text file: dashboard.spec.ts | 내부 |
| `./frontend/e2e/domain-memory.spec.ts` | TypeScript | misc | lens:제품;type:소스 | 포함 | - | 2026-01-28T17:54:02 | read-full | last: }); | TypeScript text file: domain-memory.spec.ts | 내부 |
| `./frontend/e2e/evaluation-studio.spec.ts` | TypeScript | misc | lens:제품;type:소스 | 포함 | - | 2026-01-28T17:54:02 | read-full | last: }); | TypeScript text file: evaluation-studio.spec.ts | 내부 |
| `./frontend/e2e/judge-calibration.spec.ts` | TypeScript | misc | lens:제품;type:소스 | 포함 | - | 2026-01-28T17:54:02 | read-full | last: }); | TypeScript text file: judge-calibration.spec.ts | 내부 |
| `./frontend/e2e/knowledge-base.spec.ts` | TypeScript | misc | lens:제품;type:소스 | 포함 | - | 2026-01-28T17:54:02 | read-full | last: }); | TypeScript text file: knowledge-base.spec.ts | 내부 |
| `./frontend/e2e/mocks/intents.json` | JSON | misc | lens:제품;type:소스 | 포함 | - | 2026-01-28T17:54:02 | read-full | list_len: 2; last: \] | JSON list\[2\] | 내부 |
| `./frontend/e2e/mocks/run_details.json` | JSON | misc | lens:제품;type:소스 | 포함 | - | 2026-01-28T17:54:02 | read-full | keys: summary,results; last: } | JSON object with 2 keys | 내부 |
| `./frontend/e2e/mocks/runs.json` | JSON | misc | lens:제품;type:소스 | 포함 | - | 2026-01-28T17:54:02 | read-full | list_len: 2; last: \] | JSON list\[2\] | 내부 |
| `./frontend/e2e/run-details.spec.ts` | TypeScript | misc | lens:제품;type:소스 | 포함 | - | 2026-01-28T17:54:02 | read-full | last: }); | TypeScript text file: run-details.spec.ts | 내부 |
| `./frontend/eslint.config.js` | JavaScript | misc | lens:제품;type:소스 | 포함 | - | 2026-01-28T17:54:02 | read-full | last: \]) | JavaScript text file: eslint.config.js | 내부 |
| `./frontend/index.html` | HTML | misc | lens:제품;type:소스 | 포함 | - | 2026-01-28T17:54:02 | read-full | last: </html> | HTML text file: index.html | 내부 |
| `./frontend/nginx.conf` | CONF | misc | lens:제품;type:소스 | 포함 | - | 2026-01-28T17:54:02 | binary-scan | size: 435 bytes | CONF binary file (435 bytes) | 내부 |
| `./frontend/package-lock.json` | JSON | misc | lens:제품;type:소스 | 포함 | - | 2026-01-28T17:54:02 | read-full | keys: name,version,lockfileVersion,requires,packages; last: } | JSON object with 5 keys | 내부 |
| `./frontend/package.json` | JSON | misc | lens:제품;type:소스 | 포함 | - | 2026-01-28T17:54:02 | read-full | keys: name,private,version,type,scripts,dependencies,devDependencies; last: } | JSON object with 7 keys | 내부 |
| `./frontend/playwright.config.ts` | TypeScript | misc | lens:제품;type:소스 | 포함 | - | 2026-01-28T17:54:02 | read-full | last: }); | TypeScript text file: playwright.config.ts | 내부 |
| `./frontend/public/vite.svg` | SVG | misc | lens:제품;type:소스 | 포함 | - | 2026-01-28T17:54:02 | read-full | size: 1498 bytes; last: <svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" aria-hidden="true" role="img" class=" | SVG image | 내부 |
| `./frontend/src/App.css` | CSS | code-frontend | lens:UX;type:소스 | 포함 | - | 2026-01-28T17:54:02 | read-full | last: } | CSS text file: App.css | 내부 |
| `./frontend/src/App.tsx` | TypeScript | code-frontend | lens:UX;type:소스 | 포함 | - | 2026-01-28T17:54:02 | read-full | last: export default App; | TypeScript text file: App.tsx | 내부 |
| `./frontend/src/assets/react.svg` | SVG | code-frontend | lens:UX;type:소스 | 포함 | - | 2026-01-28T17:54:02 | read-full | size: 4127 bytes; last: <svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" aria-hidden="true" role="img" class=" | SVG image | 내부 |
| `./frontend/src/components/AnalysisNodeOutputs.tsx` | TypeScript | code-frontend | lens:UX;type:소스 | 포함 | - | 2026-01-28T17:54:02 | read-full | last: } | TypeScript text file: AnalysisNodeOutputs.tsx | 내부 |
| `./frontend/src/components/InsightSpacePanel.tsx` | TypeScript | code-frontend | lens:UX;type:소스 | 포함 | - | 2026-01-28T17:54:02 | read-full | last: }; | TypeScript text file: InsightSpacePanel.tsx | 내부 |
| `./frontend/src/components/Layout.tsx` | TypeScript | code-frontend | lens:UX;type:소스 | 포함 | - | 2026-01-28T17:54:02 | read-full | last: } | TypeScript text file: Layout.tsx | 내부 |
| `./frontend/src/components/MarkdownContent.tsx` | TypeScript | code-frontend | lens:UX;type:소스 | 포함 | - | 2026-01-28T17:54:02 | read-full | last: } | TypeScript text file: MarkdownContent.tsx | 내부 |
| `./frontend/src/components/PrioritySummaryPanel.tsx` | TypeScript | code-frontend | lens:UX;type:소스 | 포함 | - | 2026-01-28T17:54:02 | read-full | last: } | TypeScript text file: PrioritySummaryPanel.tsx | 내부 |
| `./frontend/src/components/SpaceLegend.tsx` | TypeScript | code-frontend | lens:UX;type:소스 | 포함 | - | 2026-01-28T17:54:02 | read-full | last: } | TypeScript text file: SpaceLegend.tsx | 내부 |
| `./frontend/src/components/SpacePlot2D.tsx` | TypeScript | code-frontend | lens:UX;type:소스 | 포함 | - | 2026-01-28T17:54:02 | read-full | last: } | TypeScript text file: SpacePlot2D.tsx | 내부 |
| `./frontend/src/components/SpacePlot3D.tsx` | TypeScript | code-frontend | lens:UX;type:소스 | 포함 | - | 2026-01-28T17:54:02 | read-full | last: } | TypeScript text file: SpacePlot3D.tsx | 내부 |
| `./frontend/src/components/StatusBadge.tsx` | TypeScript | code-frontend | lens:UX;type:소스 | 포함 | - | 2026-01-28T17:54:02 | read-full | last: } | TypeScript text file: StatusBadge.tsx | 내부 |
| `./frontend/src/components/VirtualizedText.tsx` | TypeScript | code-frontend | lens:UX;type:소스 | 포함 | - | 2026-01-28T17:54:02 | read-full | last: } | TypeScript text file: VirtualizedText.tsx | 내부 |
| `./frontend/src/components/ai-elements/Conversation.tsx` | TypeScript | code-frontend | lens:UX;type:소스 | 포함 | - | 2026-01-28T17:54:02 | read-full | last: } | TypeScript text file: Conversation.tsx | 내부 |
| `./frontend/src/components/ai-elements/Message.tsx` | TypeScript | code-frontend | lens:UX;type:소스 | 포함 | - | 2026-01-28T17:54:02 | read-full | last: } | TypeScript text file: Message.tsx | 내부 |
| `./frontend/src/components/ai-elements/PromptInput.tsx` | TypeScript | code-frontend | lens:UX;type:소스 | 포함 | - | 2026-01-28T17:54:02 | read-full | last: } | TypeScript text file: PromptInput.tsx | 내부 |
| `./frontend/src/components/ai-elements/Response.tsx` | TypeScript | code-frontend | lens:UX;type:소스 | 포함 | - | 2026-01-28T17:54:02 | read-full | last: } | TypeScript text file: Response.tsx | 내부 |
| `./frontend/src/components/ai-elements/index.ts` | TypeScript | code-frontend | lens:UX;type:소스 | 포함 | - | 2026-01-28T17:54:02 | read-full | last: export { Response } from "./Response"; | TypeScript text file: index.ts | 내부 |
| `./frontend/src/config.ts` | TypeScript | code-frontend | lens:UX;type:소스 | 포함 | - | 2026-01-28T17:54:02 | read-full | last: export const API_BASE_URL = getApiBaseUrl(); | TypeScript text file: config.ts | 내부 |
| `./frontend/src/config/ui.ts` | TypeScript | code-frontend | lens:UX;type:소스 | 포함 | - | 2026-01-28T17:54:02 | read-full | last: export const KNOWLEDGE_BASE_BUILD_WORKERS = 4; | TypeScript text file: ui.ts | 내부 |
| `./frontend/src/hooks/useInsightSpace.ts` | TypeScript | code-frontend | lens:UX;type:소스 | 포함 | - | 2026-01-28T17:54:02 | read-full | last: } | TypeScript text file: useInsightSpace.ts | 내부 |
| `./frontend/src/index.css` | CSS | code-frontend | lens:UX;type:소스 | 포함 | - | 2026-01-28T17:54:02 | read-full | last: } | CSS text file: index.css | 내부 |
| `./frontend/src/main.tsx` | TypeScript | code-frontend | lens:UX;type:소스 | 포함 | - | 2026-01-28T17:54:02 | read-full | last: ) | TypeScript text file: main.tsx | 내부 |
| `./frontend/src/pages/AnalysisCompareView.tsx` | TypeScript | code-frontend | lens:UX;type:소스 | 포함 | - | 2026-01-28T17:54:02 | read-full | last: } | TypeScript text file: AnalysisCompareView.tsx | 내부 |
| `./frontend/src/pages/AnalysisLab.tsx` | TypeScript | code-frontend | lens:UX;type:소스 | 포함 | - | 2026-01-28T17:54:02 | read-full | last: } | TypeScript text file: AnalysisLab.tsx | 내부 |
| `./frontend/src/pages/AnalysisResultView.tsx` | TypeScript | code-frontend | lens:UX;type:소스 | 포함 | - | 2026-01-28T17:54:02 | read-full | last: } | TypeScript text file: AnalysisResultView.tsx | 내부 |
| `./frontend/src/pages/Chat.tsx` | TypeScript | code-frontend | lens:UX;type:소스 | 포함 | - | 2026-01-28T17:54:02 | read-full | last: } | TypeScript text file: Chat.tsx | 내부 |
| `./frontend/src/pages/CompareRuns.tsx` | TypeScript | code-frontend | lens:UX;type:소스 | 포함 | - | 2026-01-28T17:54:02 | read-full | last: } | TypeScript text file: CompareRuns.tsx | 내부 |
| `./frontend/src/pages/ComprehensiveAnalysis.tsx` | TypeScript | code-frontend | lens:UX;type:소스 | 포함 | - | 2026-01-28T17:54:02 | read-full | last: } | TypeScript text file: ComprehensiveAnalysis.tsx | 내부 |
| `./frontend/src/pages/CustomerReport.tsx` | TypeScript | code-frontend | lens:UX;type:소스 | 포함 | - | 2026-01-28T17:54:02 | read-full | last: } | TypeScript text file: CustomerReport.tsx | 내부 |
| `./frontend/src/pages/Dashboard.tsx` | TypeScript | code-frontend | lens:UX;type:소스 | 포함 | - | 2026-01-28T17:54:02 | read-full | last: } | TypeScript text file: Dashboard.tsx | 내부 |
| `./frontend/src/pages/DomainMemory.tsx` | TypeScript | code-frontend | lens:UX;type:소스 | 포함 | - | 2026-01-28T17:54:02 | read-full | last: } | TypeScript text file: DomainMemory.tsx | 내부 |
| `./frontend/src/pages/EvaluationStudio.tsx` | TypeScript | code-frontend | lens:UX;type:소스 | 포함 | - | 2026-01-28T17:54:02 | read-full | last: } | TypeScript text file: EvaluationStudio.tsx | 내부 |
| `./frontend/src/pages/JudgeCalibration.tsx` | TypeScript | code-frontend | lens:UX;type:소스 | 포함 | - | 2026-01-28T17:54:02 | read-full | last: } | TypeScript text file: JudgeCalibration.tsx | 내부 |
| `./frontend/src/pages/KnowledgeBase.tsx` | TypeScript | code-frontend | lens:UX;type:소스 | 포함 | - | 2026-01-28T17:54:02 | read-full | last: } | TypeScript text file: KnowledgeBase.tsx | 내부 |
| `./frontend/src/pages/RunDetails.tsx` | TypeScript | code-frontend | lens:UX;type:소스 | 포함 | - | 2026-01-28T17:54:02 | read-full | last: } | TypeScript text file: RunDetails.tsx | 내부 |
| `./frontend/src/pages/Settings.tsx` | TypeScript | code-frontend | lens:UX;type:소스 | 포함 | - | 2026-01-28T17:54:02 | read-full | last: } | TypeScript text file: Settings.tsx | 내부 |
| `./frontend/src/pages/Visualization.tsx` | TypeScript | code-frontend | lens:UX;type:소스 | 포함 | - | 2026-01-28T17:54:02 | read-full | last: } | TypeScript text file: Visualization.tsx | 내부 |
| `./frontend/src/pages/VisualizationHome.tsx` | TypeScript | code-frontend | lens:UX;type:소스 | 포함 | - | 2026-01-28T17:54:02 | read-full | last: } | TypeScript text file: VisualizationHome.tsx | 내부 |
| `./frontend/src/services/api.ts` | TypeScript | code-frontend | lens:UX;type:소스 | 포함 | - | 2026-01-28T17:54:02 | read-full | last: } | TypeScript text file: api.ts | 내부 |
| `./frontend/src/types/plotly.d.ts` | TypeScript | code-frontend | lens:UX;type:소스 | 포함 | - | 2026-01-28T17:54:02 | read-full | last: declare module "plotly.js-dist-min"; | TypeScript text file: plotly.d.ts | 내부 |
| `./frontend/src/utils/format.ts` | TypeScript | code-frontend | lens:UX;type:소스 | 포함 | - | 2026-01-28T17:54:02 | read-full | last: } | TypeScript text file: format.ts | 내부 |
| `./frontend/src/utils/phoenix.ts` | TypeScript | code-frontend | lens:UX;type:소스 | 포함 | - | 2026-01-28T17:54:02 | read-full | last: }; | TypeScript text file: phoenix.ts | 내부 |
| `./frontend/src/utils/runAnalytics.ts` | TypeScript | code-frontend | lens:UX;type:소스 | 포함 | - | 2026-01-28T17:54:02 | read-full | last: } | TypeScript text file: runAnalytics.ts | 내부 |
| `./frontend/src/utils/score.ts` | TypeScript | code-frontend | lens:UX;type:소스 | 포함 | - | 2026-01-28T17:54:02 | read-full | last: } | TypeScript text file: score.ts | 내부 |
| `./frontend/src/utils/summaryMetrics.ts` | TypeScript | code-frontend | lens:UX;type:소스 | 포함 | - | 2026-01-28T17:54:02 | read-full | last: } from "../config/ui"; | TypeScript text file: summaryMetrics.ts | 내부 |
| `./frontend/tailwind.config.js` | JavaScript | misc | lens:제품;type:소스 | 포함 | - | 2026-01-28T17:54:02 | read-full | last: } | JavaScript text file: tailwind.config.js | 내부 |
| `./frontend/tsconfig.app.json` | JSON | misc | lens:제품;type:소스 | 포함 | - | 2026-01-28T17:54:02 | manual-json-parse | parse_error; last: } | JSON parse error (manual review needed) | 내부 |
| `./frontend/tsconfig.json` | JSON | misc | lens:제품;type:소스 | 포함 | - | 2026-01-28T17:54:02 | read-full | keys: files,references; last: } | JSON object with 2 keys | 내부 |
| `./frontend/tsconfig.node.json` | JSON | misc | lens:제품;type:소스 | 포함 | - | 2026-01-28T17:54:02 | manual-json-parse | parse_error; last: } | JSON parse error (manual review needed) | 내부 |
| `./frontend/vite.config.ts` | TypeScript | misc | lens:제품;type:소스 | 포함 | - | 2026-01-28T17:54:02 | read-full | last: }) | TypeScript text file: vite.config.ts | 내부 |
| `./htmlcov/.gitignore` | File | misc | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./htmlcov/class_index.html` | HTML | misc | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./htmlcov/coverage_html_cb_6fb7b396.js` | JavaScript | misc | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./htmlcov/coverage_html_cb_bcae5fc4.js` | JavaScript | misc | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./htmlcov/favicon_32_cb_58284776.png` | PNG | misc | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./htmlcov/function_index.html` | HTML | misc | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./htmlcov/index.html` | HTML | misc | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./htmlcov/keybd_closed_cb_ce680311.png` | PNG | misc | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./htmlcov/status.json` | JSON | misc | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./htmlcov/style_cb_6b508a39.css` | CSS | misc | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./htmlcov/style_cb_a5a05ca4.css` | CSS | misc | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./htmlcov/z_09a1eb8e6cbe5399___init___py.html` | HTML | misc | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./htmlcov/z_09a1eb8e6cbe5399_base_sql_py.html` | HTML | misc | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./htmlcov/z_09a1eb8e6cbe5399_postgres_adapter_py.html` | HTML | misc | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./htmlcov/z_09a1eb8e6cbe5399_sqlite_adapter_py.html` | HTML | misc | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./htmlcov/z_15d0c774bcdd6bac___init___py.html` | HTML | misc | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./htmlcov/z_1896f08e1d9da1ef___init___py.html` | HTML | misc | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./htmlcov/z_1896f08e1d9da1ef_bm25_retriever_py.html` | HTML | misc | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./htmlcov/z_1896f08e1d9da1ef_dense_retriever_py.html` | HTML | misc | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./htmlcov/z_1896f08e1d9da1ef_document_chunker_py.html` | HTML | misc | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./htmlcov/z_1896f08e1d9da1ef_hybrid_retriever_py.html` | HTML | misc | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./htmlcov/z_1896f08e1d9da1ef_kiwi_tokenizer_py.html` | HTML | misc | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./htmlcov/z_1896f08e1d9da1ef_korean_evaluation_py.html` | HTML | misc | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./htmlcov/z_1896f08e1d9da1ef_korean_stopwords_py.html` | HTML | misc | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./htmlcov/z_1896f08e1d9da1ef_toolkit_py.html` | HTML | misc | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./htmlcov/z_19002617e05dff76___init___py.html` | HTML | misc | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./htmlcov/z_19002617e05dff76_agent_py.html` | HTML | misc | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./htmlcov/z_19002617e05dff76_analyze_py.html` | HTML | misc | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./htmlcov/z_19002617e05dff76_benchmark_py.html` | HTML | misc | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./htmlcov/z_19002617e05dff76_config_py.html` | HTML | misc | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./htmlcov/z_19002617e05dff76_domain_py.html` | HTML | misc | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./htmlcov/z_19002617e05dff76_experiment_py.html` | HTML | misc | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./htmlcov/z_19002617e05dff76_gate_py.html` | HTML | misc | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./htmlcov/z_19002617e05dff76_generate_py.html` | HTML | misc | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./htmlcov/z_19002617e05dff76_history_py.html` | HTML | misc | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./htmlcov/z_19002617e05dff76_kg_py.html` | HTML | misc | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./htmlcov/z_19002617e05dff76_langfuse_py.html` | HTML | misc | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./htmlcov/z_19002617e05dff76_pipeline_py.html` | HTML | misc | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./htmlcov/z_19002617e05dff76_run_py.html` | HTML | misc | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./htmlcov/z_19002617e05dff76_web_py.html` | HTML | misc | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./htmlcov/z_20c6c1d02076900c___init___py.html` | HTML | misc | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./htmlcov/z_20c6c1d02076900c_theme_py.html` | HTML | misc | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./htmlcov/z_2d56cdefe429235e___init___py.html` | HTML | misc | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./htmlcov/z_2d56cdefe429235e_cards_py.html` | HTML | misc | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./htmlcov/z_2d56cdefe429235e_charts_py.html` | HTML | misc | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./htmlcov/z_2d56cdefe429235e_evaluate_py.html` | HTML | misc | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./htmlcov/z_2d56cdefe429235e_history_py.html` | HTML | misc | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./htmlcov/z_2d56cdefe429235e_lists_py.html` | HTML | misc | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./htmlcov/z_2d56cdefe429235e_metrics_py.html` | HTML | misc | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./htmlcov/z_2d56cdefe429235e_progress_py.html` | HTML | misc | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./htmlcov/z_2d56cdefe429235e_reports_py.html` | HTML | misc | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./htmlcov/z_2d56cdefe429235e_stats_py.html` | HTML | misc | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./htmlcov/z_2d56cdefe429235e_upload_py.html` | HTML | misc | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./htmlcov/z_307c0430633cfe24___init___py.html` | HTML | misc | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./htmlcov/z_307c0430633cfe24_insight_generator_py.html` | HTML | misc | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./htmlcov/z_307c0430633cfe24_pattern_detector_py.html` | HTML | misc | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./htmlcov/z_307c0430633cfe24_playbook_loader_py.html` | HTML | misc | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./htmlcov/z_354ee341f7b1ed39___init___py.html` | HTML | misc | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./htmlcov/z_354ee341f7b1ed39_sqlite_adapter_py.html` | HTML | misc | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./htmlcov/z_45fd31b21b5db4a9___init___py.html` | HTML | misc | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./htmlcov/z_45fd31b21b5db4a9_llm_report_generator_py.html` | HTML | misc | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./htmlcov/z_45fd31b21b5db4a9_markdown_adapter_py.html` | HTML | misc | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./htmlcov/z_4c03e7fdb49adcce___init___py.html` | HTML | misc | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./htmlcov/z_4c03e7fdb49adcce_cli_py.html` | HTML | misc | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./htmlcov/z_6ef5e8a36594507c___init___py.html` | HTML | misc | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./htmlcov/z_6ef5e8a36594507c_analysis_pipeline_py.html` | HTML | misc | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./htmlcov/z_6ef5e8a36594507c_analysis_py.html` | HTML | misc | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./htmlcov/z_6ef5e8a36594507c_benchmark_py.html` | HTML | misc | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./htmlcov/z_6ef5e8a36594507c_dataset_py.html` | HTML | misc | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./htmlcov/z_6ef5e8a36594507c_experiment_py.html` | HTML | misc | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./htmlcov/z_6ef5e8a36594507c_improvement_py.html` | HTML | misc | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./htmlcov/z_6ef5e8a36594507c_kg_py.html` | HTML | misc | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./htmlcov/z_6ef5e8a36594507c_memory_py.html` | HTML | misc | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./htmlcov/z_6ef5e8a36594507c_rag_trace_py.html` | HTML | misc | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./htmlcov/z_6ef5e8a36594507c_result_py.html` | HTML | misc | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./htmlcov/z_706276de613709ef___init___py.html` | HTML | misc | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./htmlcov/z_706276de613709ef_anthropic_adapter_py.html` | HTML | misc | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./htmlcov/z_706276de613709ef_azure_adapter_py.html` | HTML | misc | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./htmlcov/z_706276de613709ef_base_py.html` | HTML | misc | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./htmlcov/z_706276de613709ef_llm_relation_augmenter_py.html` | HTML | misc | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./htmlcov/z_706276de613709ef_ollama_adapter_py.html` | HTML | misc | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./htmlcov/z_706276de613709ef_openai_adapter_py.html` | HTML | misc | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./htmlcov/z_706276de613709ef_token_aware_chat_py.html` | HTML | misc | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./htmlcov/z_8ab9a5c51a8689a0___init___py.html` | HTML | misc | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./htmlcov/z_8ab9a5c51a8689a0_analysis_service_py.html` | HTML | misc | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./htmlcov/z_8ab9a5c51a8689a0_batch_executor_py.html` | HTML | misc | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./htmlcov/z_8ab9a5c51a8689a0_benchmark_runner_py.html` | HTML | misc | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./htmlcov/z_8ab9a5c51a8689a0_document_chunker_py.html` | HTML | misc | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./htmlcov/z_8ab9a5c51a8689a0_domain_learning_hook_py.html` | HTML | misc | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./htmlcov/z_8ab9a5c51a8689a0_entity_extractor_py.html` | HTML | misc | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./htmlcov/z_8ab9a5c51a8689a0_evaluator_py.html` | HTML | misc | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./htmlcov/z_8ab9a5c51a8689a0_experiment_manager_py.html` | HTML | misc | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./htmlcov/z_8ab9a5c51a8689a0_improvement_guide_service_py.html` | HTML | misc | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./htmlcov/z_8ab9a5c51a8689a0_intent_classifier_py.html` | HTML | misc | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./htmlcov/z_8ab9a5c51a8689a0_kg_generator_py.html` | HTML | misc | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./htmlcov/z_8ab9a5c51a8689a0_memory_aware_evaluator_py.html` | HTML | misc | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./htmlcov/z_8ab9a5c51a8689a0_memory_based_analysis_py.html` | HTML | misc | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./htmlcov/z_8ab9a5c51a8689a0_pipeline_orchestrator_py.html` | HTML | misc | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./htmlcov/z_8ab9a5c51a8689a0_pipeline_template_registry_py.html` | HTML | misc | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./htmlcov/z_8ab9a5c51a8689a0_testset_generator_py.html` | HTML | misc | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./htmlcov/z_8f8456551edf1193___init___py.html` | HTML | misc | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./htmlcov/z_9c2203071244a422___init___py.html` | HTML | misc | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./htmlcov/z_ae47c9b820c840f4___init___py.html` | HTML | misc | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./htmlcov/z_ae47c9b820c840f4_langfuse_adapter_py.html` | HTML | misc | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./htmlcov/z_ae47c9b820c840f4_mlflow_adapter_py.html` | HTML | misc | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./htmlcov/z_ae47c9b820c840f4_phoenix_adapter_py.html` | HTML | misc | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./htmlcov/z_af18d2f1810e66bd___init___py.html` | HTML | misc | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./htmlcov/z_b8ea285b79335352___init___py.html` | HTML | misc | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./htmlcov/z_b8ea285b79335352_formatters_py.html` | HTML | misc | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./htmlcov/z_b8ea285b79335352_options_py.html` | HTML | misc | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./htmlcov/z_b8ea285b79335352_validators_py.html` | HTML | misc | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./htmlcov/z_bf0ff448b6346c7b___init___py.html` | HTML | misc | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./htmlcov/z_bf0ff448b6346c7b_adapter_py.html` | HTML | misc | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./htmlcov/z_bf0ff448b6346c7b_app_py.html` | HTML | misc | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./htmlcov/z_bf0ff448b6346c7b_session_py.html` | HTML | misc | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./htmlcov/z_c503ad3c05f061fe___init___py.html` | HTML | misc | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./htmlcov/z_c60a5984f1f262ae___init___py.html` | HTML | misc | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./htmlcov/z_c60a5984f1f262ae_memory_cache_py.html` | HTML | misc | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./htmlcov/z_cf913e7f461137cc___init___py.html` | HTML | misc | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./htmlcov/z_d5db758984fd2c73___init___py.html` | HTML | misc | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./htmlcov/z_d5db758984fd2c73_app_py.html` | HTML | misc | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./htmlcov/z_d7401fdcbfb3676e___init___py.html` | HTML | misc | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./htmlcov/z_dc78805f3d415bd4___init___py.html` | HTML | misc | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./htmlcov/z_dc78805f3d415bd4_agent_types_py.html` | HTML | misc | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./htmlcov/z_dc78805f3d415bd4_domain_config_py.html` | HTML | misc | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./htmlcov/z_dc78805f3d415bd4_instrumentation_py.html` | HTML | misc | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./htmlcov/z_dc78805f3d415bd4_model_config_py.html` | HTML | misc | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./htmlcov/z_dc78805f3d415bd4_settings_py.html` | HTML | misc | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./htmlcov/z_dd9f472a22bdd3cb___init___py.html` | HTML | misc | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./htmlcov/z_dd9f472a22bdd3cb_analysis_cache_port_py.html` | HTML | misc | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./htmlcov/z_dd9f472a22bdd3cb_analysis_module_port_py.html` | HTML | misc | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./htmlcov/z_dd9f472a22bdd3cb_analysis_port_py.html` | HTML | misc | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./htmlcov/z_dd9f472a22bdd3cb_causal_analysis_port_py.html` | HTML | misc | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./htmlcov/z_dd9f472a22bdd3cb_dataset_port_py.html` | HTML | misc | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./htmlcov/z_dd9f472a22bdd3cb_domain_memory_port_py.html` | HTML | misc | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./htmlcov/z_dd9f472a22bdd3cb_embedding_port_py.html` | HTML | misc | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./htmlcov/z_dd9f472a22bdd3cb_improvement_port_py.html` | HTML | misc | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./htmlcov/z_dd9f472a22bdd3cb_intent_classifier_port_py.html` | HTML | misc | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./htmlcov/z_dd9f472a22bdd3cb_korean_nlp_port_py.html` | HTML | misc | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./htmlcov/z_dd9f472a22bdd3cb_llm_port_py.html` | HTML | misc | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./htmlcov/z_dd9f472a22bdd3cb_nlp_analysis_port_py.html` | HTML | misc | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./htmlcov/z_dd9f472a22bdd3cb_relation_augmenter_port_py.html` | HTML | misc | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./htmlcov/z_dd9f472a22bdd3cb_report_port_py.html` | HTML | misc | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./htmlcov/z_dd9f472a22bdd3cb_storage_port_py.html` | HTML | misc | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./htmlcov/z_dd9f472a22bdd3cb_tracker_port_py.html` | HTML | misc | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./htmlcov/z_eed2f4e786e833c2___init___py.html` | HTML | misc | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./htmlcov/z_eed2f4e786e833c2_analysis_pipeline_port_py.html` | HTML | misc | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./htmlcov/z_eed2f4e786e833c2_evaluator_port_py.html` | HTML | misc | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./htmlcov/z_eed2f4e786e833c2_learning_hook_port_py.html` | HTML | misc | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./htmlcov/z_eed2f4e786e833c2_web_port_py.html` | HTML | misc | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./htmlcov/z_f2babf63a4f78925___init___py.html` | HTML | misc | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./htmlcov/z_f2babf63a4f78925_analysis_report_module_py.html` | HTML | misc | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./htmlcov/z_f2babf63a4f78925_base_module_py.html` | HTML | misc | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./htmlcov/z_f2babf63a4f78925_causal_adapter_py.html` | HTML | misc | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./htmlcov/z_f2babf63a4f78925_causal_analyzer_module_py.html` | HTML | misc | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./htmlcov/z_f2babf63a4f78925_common_py.html` | HTML | misc | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./htmlcov/z_f2babf63a4f78925_comparison_report_module_py.html` | HTML | misc | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./htmlcov/z_f2babf63a4f78925_data_loader_module_py.html` | HTML | misc | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./htmlcov/z_f2babf63a4f78925_nlp_adapter_py.html` | HTML | misc | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./htmlcov/z_f2babf63a4f78925_nlp_analyzer_module_py.html` | HTML | misc | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./htmlcov/z_f2babf63a4f78925_statistical_adapter_py.html` | HTML | misc | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./htmlcov/z_f2babf63a4f78925_statistical_analyzer_module_py.html` | HTML | misc | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./htmlcov/z_f2babf63a4f78925_summary_report_module_py.html` | HTML | misc | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./htmlcov/z_f2babf63a4f78925_verification_report_module_py.html` | HTML | misc | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./htmlcov/z_f850069011182385___init___py.html` | HTML | misc | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./htmlcov/z_f850069011182385_insurance_py.html` | HTML | misc | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./htmlcov/z_ff13382c39ff3e3e___init___py.html` | HTML | misc | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./htmlcov/z_ff13382c39ff3e3e_base_py.html` | HTML | misc | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./htmlcov/z_ff13382c39ff3e3e_csv_loader_py.html` | HTML | misc | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./htmlcov/z_ff13382c39ff3e3e_excel_loader_py.html` | HTML | misc | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./htmlcov/z_ff13382c39ff3e3e_json_loader_py.html` | HTML | misc | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./htmlcov/z_ff13382c39ff3e3e_loader_factory_py.html` | HTML | misc | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./mkdocs.yml` | YAML | misc | lens:제품;type:소스 | 포함 | - | 2026-01-28T17:54:02 | read-full | last:   - stylesheets/extra.css | YAML text file: mkdocs.yml | 내부 |
| `./package-lock.json` | JSON | misc | lens:제품;type:소스 | 포함 | - | 2026-01-28T17:54:02 | read-full | keys: name,lockfileVersion,requires,packages; last: } | JSON object with 4 keys | 내부 |
| `./prompts/system_override.txt` | Text | misc | lens:제품;type:소스 | 포함 | - | 2026-01-28T17:54:02 | read-full | last: 너는 정확한 지식 기반의 도우미다. 질문에 대해 간결하고 근거 중심으로 답하라. | Text text file: system_override.txt | 내부 |
| `./pyproject.toml` | TOML | infra | lens:운영;type:설정 | 포함 | - | 2026-01-28T17:54:02 | read-full | last: upload_to_vcs_release = true | TOML text file: pyproject.toml | 내부 |
| `./reports/.gitkeep` | File | reports | lens:QA;type:보고서 | 포함 | - | 2026-01-28T17:54:02 | binary-scan | size: 86 bytes | File binary file (86 bytes) | 내부 |
| `./reports/README.md` | Markdown | reports | lens:QA;type:보고서 | 포함 | - | 2026-01-28T17:54:02 | read-full | last: - \[STRUCTURE_REVIEW.md\](../STRUCTURE_REVIEW.md) - 프로젝트 구조 리뷰 | Markdown text file: Reports | 내부 |
| `./reports/analysis/analysis_0aa9fab0-6c2c-4c1c-b228-202a38a2f00c.json` | JSON | reports | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./reports/analysis/analysis_0aa9fab0-6c2c-4c1c-b228-202a38a2f00c.md` | Markdown | reports | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./reports/analysis/analysis_2163f844-ee2c-4630-9ba8-35cd9954d92e.json` | JSON | reports | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./reports/analysis/analysis_2163f844-ee2c-4630-9ba8-35cd9954d92e.md` | Markdown | reports | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./reports/analysis/analysis_4516d358-2797-4c46-9f14-c1d975588025.json` | JSON | reports | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./reports/analysis/analysis_4516d358-2797-4c46-9f14-c1d975588025.md` | Markdown | reports | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./reports/analysis/analysis_4792d785-a8ea-4fd3-8a0c-dcbf1889f5fb.json` | JSON | reports | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./reports/analysis/analysis_4792d785-a8ea-4fd3-8a0c-dcbf1889f5fb.md` | Markdown | reports | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./reports/analysis/analysis_8f825b22-87f1-4d9b-b3a0-8ff65dbec2c5.json` | JSON | reports | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./reports/analysis/analysis_8f825b22-87f1-4d9b-b3a0-8ff65dbec2c5.md` | Markdown | reports | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./reports/analysis/analysis_9fbf4776-9f5b-4c4b-ba08-c556032cee86.json` | JSON | reports | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./reports/analysis/analysis_9fbf4776-9f5b-4c4b-ba08-c556032cee86.md` | Markdown | reports | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./reports/analysis/analysis_e2f7e6bb-a86e-4f6a-8002-0c6f1a831775.json` | JSON | reports | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./reports/analysis/analysis_e2f7e6bb-a86e-4f6a-8002-0c6f1a831775.md` | Markdown | reports | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./reports/analysis/analysis_f1287e90-43b6-42c8-b3ac-e6cb3e06a71e.json` | JSON | reports | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./reports/analysis/analysis_f1287e90-43b6-42c8-b3ac-e6cb3e06a71e.md` | Markdown | reports | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./reports/analysis/artifacts/analysis_4516d358-2797-4c46-9f14-c1d975588025/causal_analysis.json` | JSON | reports | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./reports/analysis/artifacts/analysis_4516d358-2797-4c46-9f14-c1d975588025/diagnostic.json` | JSON | reports | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./reports/analysis/artifacts/analysis_4516d358-2797-4c46-9f14-c1d975588025/final_output.json` | JSON | reports | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./reports/analysis/artifacts/analysis_4516d358-2797-4c46-9f14-c1d975588025/index.json` | JSON | reports | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./reports/analysis/artifacts/analysis_4516d358-2797-4c46-9f14-c1d975588025/load_data.json` | JSON | reports | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./reports/analysis/artifacts/analysis_4516d358-2797-4c46-9f14-c1d975588025/load_runs.json` | JSON | reports | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./reports/analysis/artifacts/analysis_4516d358-2797-4c46-9f14-c1d975588025/low_samples.json` | JSON | reports | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./reports/analysis/artifacts/analysis_4516d358-2797-4c46-9f14-c1d975588025/nlp_analysis.json` | JSON | reports | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./reports/analysis/artifacts/analysis_4516d358-2797-4c46-9f14-c1d975588025/pattern_detection.json` | JSON | reports | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./reports/analysis/artifacts/analysis_4516d358-2797-4c46-9f14-c1d975588025/priority_summary.json` | JSON | reports | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./reports/analysis/artifacts/analysis_4516d358-2797-4c46-9f14-c1d975588025/ragas_eval.json` | JSON | reports | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./reports/analysis/artifacts/analysis_4516d358-2797-4c46-9f14-c1d975588025/report.json` | JSON | reports | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./reports/analysis/artifacts/analysis_4516d358-2797-4c46-9f14-c1d975588025/root_cause.json` | JSON | reports | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./reports/analysis/artifacts/analysis_4516d358-2797-4c46-9f14-c1d975588025/statistics.json` | JSON | reports | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./reports/analysis/artifacts/analysis_4516d358-2797-4c46-9f14-c1d975588025/time_series.json` | JSON | reports | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./reports/analysis/artifacts/analysis_4516d358-2797-4c46-9f14-c1d975588025/trend_detection.json` | JSON | reports | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./reports/analysis/artifacts/analysis_4792d785-a8ea-4fd3-8a0c-dcbf1889f5fb/causal_analysis.json` | JSON | reports | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./reports/analysis/artifacts/analysis_4792d785-a8ea-4fd3-8a0c-dcbf1889f5fb/diagnostic.json` | JSON | reports | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./reports/analysis/artifacts/analysis_4792d785-a8ea-4fd3-8a0c-dcbf1889f5fb/final_output.json` | JSON | reports | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./reports/analysis/artifacts/analysis_4792d785-a8ea-4fd3-8a0c-dcbf1889f5fb/index.json` | JSON | reports | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./reports/analysis/artifacts/analysis_4792d785-a8ea-4fd3-8a0c-dcbf1889f5fb/load_data.json` | JSON | reports | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./reports/analysis/artifacts/analysis_4792d785-a8ea-4fd3-8a0c-dcbf1889f5fb/load_runs.json` | JSON | reports | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./reports/analysis/artifacts/analysis_4792d785-a8ea-4fd3-8a0c-dcbf1889f5fb/low_samples.json` | JSON | reports | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./reports/analysis/artifacts/analysis_4792d785-a8ea-4fd3-8a0c-dcbf1889f5fb/nlp_analysis.json` | JSON | reports | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./reports/analysis/artifacts/analysis_4792d785-a8ea-4fd3-8a0c-dcbf1889f5fb/pattern_detection.json` | JSON | reports | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./reports/analysis/artifacts/analysis_4792d785-a8ea-4fd3-8a0c-dcbf1889f5fb/priority_summary.json` | JSON | reports | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./reports/analysis/artifacts/analysis_4792d785-a8ea-4fd3-8a0c-dcbf1889f5fb/ragas_eval.json` | JSON | reports | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./reports/analysis/artifacts/analysis_4792d785-a8ea-4fd3-8a0c-dcbf1889f5fb/report.json` | JSON | reports | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./reports/analysis/artifacts/analysis_4792d785-a8ea-4fd3-8a0c-dcbf1889f5fb/root_cause.json` | JSON | reports | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./reports/analysis/artifacts/analysis_4792d785-a8ea-4fd3-8a0c-dcbf1889f5fb/statistics.json` | JSON | reports | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./reports/analysis/artifacts/analysis_4792d785-a8ea-4fd3-8a0c-dcbf1889f5fb/time_series.json` | JSON | reports | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./reports/analysis/artifacts/analysis_4792d785-a8ea-4fd3-8a0c-dcbf1889f5fb/trend_detection.json` | JSON | reports | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./reports/analysis/artifacts/analysis_8f825b22-87f1-4d9b-b3a0-8ff65dbec2c5/causal_analysis.json` | JSON | reports | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./reports/analysis/artifacts/analysis_8f825b22-87f1-4d9b-b3a0-8ff65dbec2c5/diagnostic.json` | JSON | reports | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./reports/analysis/artifacts/analysis_8f825b22-87f1-4d9b-b3a0-8ff65dbec2c5/final_output.json` | JSON | reports | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./reports/analysis/artifacts/analysis_8f825b22-87f1-4d9b-b3a0-8ff65dbec2c5/index.json` | JSON | reports | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./reports/analysis/artifacts/analysis_8f825b22-87f1-4d9b-b3a0-8ff65dbec2c5/load_data.json` | JSON | reports | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./reports/analysis/artifacts/analysis_8f825b22-87f1-4d9b-b3a0-8ff65dbec2c5/load_runs.json` | JSON | reports | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./reports/analysis/artifacts/analysis_8f825b22-87f1-4d9b-b3a0-8ff65dbec2c5/low_samples.json` | JSON | reports | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./reports/analysis/artifacts/analysis_8f825b22-87f1-4d9b-b3a0-8ff65dbec2c5/nlp_analysis.json` | JSON | reports | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./reports/analysis/artifacts/analysis_8f825b22-87f1-4d9b-b3a0-8ff65dbec2c5/pattern_detection.json` | JSON | reports | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./reports/analysis/artifacts/analysis_8f825b22-87f1-4d9b-b3a0-8ff65dbec2c5/priority_summary.json` | JSON | reports | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./reports/analysis/artifacts/analysis_8f825b22-87f1-4d9b-b3a0-8ff65dbec2c5/ragas_eval.json` | JSON | reports | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./reports/analysis/artifacts/analysis_8f825b22-87f1-4d9b-b3a0-8ff65dbec2c5/report.json` | JSON | reports | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./reports/analysis/artifacts/analysis_8f825b22-87f1-4d9b-b3a0-8ff65dbec2c5/root_cause.json` | JSON | reports | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./reports/analysis/artifacts/analysis_8f825b22-87f1-4d9b-b3a0-8ff65dbec2c5/statistics.json` | JSON | reports | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./reports/analysis/artifacts/analysis_8f825b22-87f1-4d9b-b3a0-8ff65dbec2c5/time_series.json` | JSON | reports | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./reports/analysis/artifacts/analysis_8f825b22-87f1-4d9b-b3a0-8ff65dbec2c5/trend_detection.json` | JSON | reports | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./reports/analysis/artifacts/analysis_e2f7e6bb-a86e-4f6a-8002-0c6f1a831775/causal_analysis.json` | JSON | reports | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./reports/analysis/artifacts/analysis_e2f7e6bb-a86e-4f6a-8002-0c6f1a831775/diagnostic.json` | JSON | reports | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./reports/analysis/artifacts/analysis_e2f7e6bb-a86e-4f6a-8002-0c6f1a831775/final_output.json` | JSON | reports | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./reports/analysis/artifacts/analysis_e2f7e6bb-a86e-4f6a-8002-0c6f1a831775/index.json` | JSON | reports | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./reports/analysis/artifacts/analysis_e2f7e6bb-a86e-4f6a-8002-0c6f1a831775/load_data.json` | JSON | reports | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./reports/analysis/artifacts/analysis_e2f7e6bb-a86e-4f6a-8002-0c6f1a831775/load_runs.json` | JSON | reports | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./reports/analysis/artifacts/analysis_e2f7e6bb-a86e-4f6a-8002-0c6f1a831775/low_samples.json` | JSON | reports | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./reports/analysis/artifacts/analysis_e2f7e6bb-a86e-4f6a-8002-0c6f1a831775/nlp_analysis.json` | JSON | reports | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./reports/analysis/artifacts/analysis_e2f7e6bb-a86e-4f6a-8002-0c6f1a831775/pattern_detection.json` | JSON | reports | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./reports/analysis/artifacts/analysis_e2f7e6bb-a86e-4f6a-8002-0c6f1a831775/priority_summary.json` | JSON | reports | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./reports/analysis/artifacts/analysis_e2f7e6bb-a86e-4f6a-8002-0c6f1a831775/ragas_eval.json` | JSON | reports | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./reports/analysis/artifacts/analysis_e2f7e6bb-a86e-4f6a-8002-0c6f1a831775/report.json` | JSON | reports | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./reports/analysis/artifacts/analysis_e2f7e6bb-a86e-4f6a-8002-0c6f1a831775/root_cause.json` | JSON | reports | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./reports/analysis/artifacts/analysis_e2f7e6bb-a86e-4f6a-8002-0c6f1a831775/statistics.json` | JSON | reports | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./reports/analysis/artifacts/analysis_e2f7e6bb-a86e-4f6a-8002-0c6f1a831775/time_series.json` | JSON | reports | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./reports/analysis/artifacts/analysis_e2f7e6bb-a86e-4f6a-8002-0c6f1a831775/trend_detection.json` | JSON | reports | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./reports/analysis/artifacts/analysis_f1287e90-43b6-42c8-b3ac-e6cb3e06a71e/causal_analysis.json` | JSON | reports | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./reports/analysis/artifacts/analysis_f1287e90-43b6-42c8-b3ac-e6cb3e06a71e/diagnostic.json` | JSON | reports | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./reports/analysis/artifacts/analysis_f1287e90-43b6-42c8-b3ac-e6cb3e06a71e/final_output.json` | JSON | reports | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./reports/analysis/artifacts/analysis_f1287e90-43b6-42c8-b3ac-e6cb3e06a71e/index.json` | JSON | reports | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./reports/analysis/artifacts/analysis_f1287e90-43b6-42c8-b3ac-e6cb3e06a71e/load_data.json` | JSON | reports | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./reports/analysis/artifacts/analysis_f1287e90-43b6-42c8-b3ac-e6cb3e06a71e/load_runs.json` | JSON | reports | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./reports/analysis/artifacts/analysis_f1287e90-43b6-42c8-b3ac-e6cb3e06a71e/low_samples.json` | JSON | reports | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./reports/analysis/artifacts/analysis_f1287e90-43b6-42c8-b3ac-e6cb3e06a71e/nlp_analysis.json` | JSON | reports | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./reports/analysis/artifacts/analysis_f1287e90-43b6-42c8-b3ac-e6cb3e06a71e/pattern_detection.json` | JSON | reports | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./reports/analysis/artifacts/analysis_f1287e90-43b6-42c8-b3ac-e6cb3e06a71e/priority_summary.json` | JSON | reports | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./reports/analysis/artifacts/analysis_f1287e90-43b6-42c8-b3ac-e6cb3e06a71e/ragas_eval.json` | JSON | reports | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./reports/analysis/artifacts/analysis_f1287e90-43b6-42c8-b3ac-e6cb3e06a71e/report.json` | JSON | reports | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./reports/analysis/artifacts/analysis_f1287e90-43b6-42c8-b3ac-e6cb3e06a71e/root_cause.json` | JSON | reports | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./reports/analysis/artifacts/analysis_f1287e90-43b6-42c8-b3ac-e6cb3e06a71e/statistics.json` | JSON | reports | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./reports/analysis/artifacts/analysis_f1287e90-43b6-42c8-b3ac-e6cb3e06a71e/time_series.json` | JSON | reports | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./reports/analysis/artifacts/analysis_f1287e90-43b6-42c8-b3ac-e6cb3e06a71e/trend_detection.json` | JSON | reports | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./reports/comparison/artifacts/comparison_0aa9fab0_f1287e90/final_output.json` | JSON | reports | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./reports/comparison/artifacts/comparison_0aa9fab0_f1287e90/index.json` | JSON | reports | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./reports/comparison/artifacts/comparison_0aa9fab0_f1287e90/load_runs.json` | JSON | reports | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./reports/comparison/artifacts/comparison_0aa9fab0_f1287e90/report.json` | JSON | reports | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./reports/comparison/artifacts/comparison_0aa9fab0_f1287e90/run_change_detection.json` | JSON | reports | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./reports/comparison/artifacts/comparison_0aa9fab0_f1287e90/run_metric_comparison.json` | JSON | reports | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./reports/comparison/artifacts/comparison_8f825b22_4516d358/final_output.json` | JSON | reports | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./reports/comparison/artifacts/comparison_8f825b22_4516d358/index.json` | JSON | reports | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./reports/comparison/artifacts/comparison_8f825b22_4516d358/load_runs.json` | JSON | reports | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./reports/comparison/artifacts/comparison_8f825b22_4516d358/report.json` | JSON | reports | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./reports/comparison/artifacts/comparison_8f825b22_4516d358/run_change_detection.json` | JSON | reports | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./reports/comparison/artifacts/comparison_8f825b22_4516d358/run_metric_comparison.json` | JSON | reports | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./reports/comparison/artifacts/comparison_f1287e90_8f825b22/final_output.json` | JSON | reports | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./reports/comparison/artifacts/comparison_f1287e90_8f825b22/index.json` | JSON | reports | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./reports/comparison/artifacts/comparison_f1287e90_8f825b22/load_runs.json` | JSON | reports | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./reports/comparison/artifacts/comparison_f1287e90_8f825b22/report.json` | JSON | reports | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./reports/comparison/artifacts/comparison_f1287e90_8f825b22/run_change_detection.json` | JSON | reports | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./reports/comparison/artifacts/comparison_f1287e90_8f825b22/run_metric_comparison.json` | JSON | reports | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./reports/comparison/artifacts/comparison_run-1_run-2/final_output.json` | JSON | reports | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./reports/comparison/artifacts/comparison_run-1_run-2/index.json` | JSON | reports | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./reports/comparison/comparison_0aa9fab0_9fbf4776.json` | JSON | reports | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./reports/comparison/comparison_0aa9fab0_9fbf4776.md` | Markdown | reports | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./reports/comparison/comparison_0aa9fab0_f1287e90.json` | JSON | reports | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./reports/comparison/comparison_0aa9fab0_f1287e90.md` | Markdown | reports | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./reports/comparison/comparison_8f825b22_4516d358.json` | JSON | reports | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./reports/comparison/comparison_8f825b22_4516d358.md` | Markdown | reports | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./reports/comparison/comparison_9fbf4776_a491fa0e.json` | JSON | reports | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./reports/comparison/comparison_9fbf4776_a491fa0e.md` | Markdown | reports | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./reports/comparison/comparison_f1287e90_8f825b22.json` | JSON | reports | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./reports/comparison/comparison_f1287e90_8f825b22.md` | Markdown | reports | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./reports/comparison/comparison_run-1_run-2.json` | JSON | reports | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./reports/comparison/comparison_run-1_run-2.md` | Markdown | reports | pending | 제외 | 실행 산출물 디렉터리 | - | - | - | - | - |
| `./reports/debug_report_r1_smoke.md` | Markdown | reports | lens:QA;type:보고서 | 포함 | - | 2026-01-28T17:54:02 | read-full | last: - retrieval.score_gap: score=0.08292250839768633 threshold=0.1 stage_id=423de2bd-1b6c-4b6c-bd44-33a36e7e6da9 | Markdown text file: Debug Report | 내부 |
| `./reports/debug_report_r2_graphrag.md` | Markdown | reports | lens:QA;type:보고서 | 포함 | - | 2026-01-28T17:54:02 | read-full | last: - retrieval.score_gap: score=0.00018508725542041443 threshold=0.1 stage_id=89d58c61-1df9-4670-9776-b54b5adb68de | Markdown text file: Debug Report | 내부 |
| `./reports/debug_report_r2_graphrag_openai.md` | Markdown | reports | lens:QA;type:보고서 | 포함 | - | 2026-01-28T17:54:02 | read-full | last: - retrieval.score_gap: score=0.00018508725542041443 threshold=0.1 stage_id=0c97b847-2fee-4bb4-8b56-b24d6193b8c1 | Markdown text file: Debug Report | 내부 |
| `./reports/debug_report_r3_bm25.md` | Markdown | reports | lens:QA;type:보고서 | 포함 | - | 2026-01-28T17:54:02 | read-full | last: - retrieval.score_gap: score=0.0 threshold=0.1 stage_id=5dfeebb1-5362-46c1-acbb-95860a51cc94 | Markdown text file: Debug Report | 내부 |
| `./reports/debug_report_r3_bm25_langfuse3.md` | Markdown | reports | lens:QA;type:보고서 | 포함 | - | 2026-01-28T17:54:02 | read-full | last: - retrieval.score_gap: score=0.0 threshold=0.1 stage_id=c66c049c-2e92-4e2a-ba3c-8e966101363a | Markdown text file: Debug Report | 내부 |
| `./reports/debug_report_r3_dense_faiss.md` | Markdown | reports | lens:QA;type:보고서 | 포함 | - | 2026-01-28T17:54:02 | read-full | last: - retrieval.latency_ms: score=724.6685000136495 threshold=500.0 stage_id=205a6579-835f-42f7-9bde-cf21ac3ed2ff | Markdown text file: Debug Report | 내부 |
| `./reports/feature_verification_report.md` | Markdown | reports | lens:QA;type:보고서 | 포함 | - | 2026-01-28T17:54:02 | read-full | last: *본 보고서는 2026-01-27 기준 EvalVault v1.69.0을 대상으로 작성되었습니다.* | Markdown text file: EvalVault 기능 종합 검증 보고서 | 내부 |
| `./reports/graphrag_compare.json` | JSON | reports | lens:QA;type:보고서 | 포함 | - | 2026-01-28T17:54:02 | read-full | keys: baseline,graph,comparisons,graph_contexts,graph_subgraphs,retriever_doc_ids; last: } | JSON object with 6 keys | 내부 |
| `./reports/graphrag_compare_qwen3_14b.json` | JSON | reports | lens:QA;type:보고서 | 포함 | - | 2026-01-28T17:54:02 | read-full | keys: baseline,graph,comparisons,graph_contexts,graph_subgraphs,retriever_doc_ids; last: } | JSON object with 6 keys | 내부 |
| `./reports/graphrag_compare_qwen3_14b_multi_faithfulness.json` | JSON | reports | lens:QA;type:보고서 | 포함 | - | 2026-01-28T17:54:02 | read-full | keys: baseline,graph,comparisons,graph_contexts,graph_subgraphs,retriever_doc_ids; last: } | JSON object with 6 keys | 내부 |
| `./reports/improvement_1d91a667-4288-4742-be3a-a8f5310c5140.md` | Markdown | reports | lens:QA;type:보고서 | 포함 | - | 2026-01-28T17:54:02 | read-full | last: *Generated by EvalVault* | Markdown text file: EvalVault Analysis Report | 내부 |
| `./reports/presentation_materials_final.md` | Markdown | reports | lens:QA;type:보고서 | 포함 | - | 2026-01-28T17:54:02 | read-full | last: **감사합니다!** | Markdown text file: EvalVault 발표용 자료 최종본 | 내부 |
| `./reports/presentation_materials_phase1.md` | Markdown | reports | lens:QA;type:보고서 | 포함 | - | 2026-01-28T17:54:02 | read-full | last: - .github/workflows/ci.yml | Markdown text file: EvalVault 발표용 자료 수집 - 1단계: 프로젝트 개요 | 내부 |
| `./reports/presentation_materials_phase2.md` | Markdown | reports | lens:QA;type:보고서 | 포함 | - | 2026-01-28T17:54:02 | read-full | last: - AGENTS.md | Markdown text file: EvalVault 발표용 자료 수집 - 2단계: 업무 자동화 사례 | 내부 |
| `./reports/presentation_materials_verification.md` | Markdown | reports | lens:QA;type:보고서 | 포함 | - | 2026-01-28T17:54:02 | read-full | last: **발표 준비 완료** 🎉 | Markdown text file: 발표용 자료 최종 검증 보고서 | 내부 |
| `./reports/r2_graphrag_openai_stage_events.jsonl` | JSONL | reports | lens:QA;type:보고서 | 포함 | - | 2026-01-28T17:54:02 | read-full | lines: 3; last: {"run_id": "fd810155-d69f-4c2c-944a-be960a32aa62", "stage_id": "972d6e13-bf1f-4e52-b1e9-76f969e268e0", "parent_stage_id" | JSONL lines=3 | 내부 |
| `./reports/r2_graphrag_openai_stage_report.txt` | Text | reports | lens:QA;type:보고서 | 포함 | - | 2026-01-28T17:54:02 | read-full | last: └───────────┴───────────┴──────────────────────┴────────┴──────────────────────┘ | Text text file: r2_graphrag_openai_stage_report.txt | 내부 |
| `./reports/r2_graphrag_stage_events.jsonl` | JSONL | reports | lens:QA;type:보고서 | 포함 | - | 2026-01-28T17:54:02 | read-full | lines: 3; last: {"run_id": "d60bce6a-ce38-4210-a63e-c8d73d9ecfe7", "stage_id": "e1597937-6d86-42d2-8132-54207c54a428", "parent_stage_id" | JSONL lines=3 | 내부 |
| `./reports/r2_graphrag_stage_report.txt` | Text | reports | lens:QA;type:보고서 | 포함 | - | 2026-01-28T17:54:02 | read-full | last: └───────────┴──────────┴──────────────────────┴────────┴──────────────────────┘ | Text text file: r2_graphrag_stage_report.txt | 내부 |
| `./reports/r3_bm25_langfuse2_stage_events.jsonl` | JSONL | reports | lens:QA;type:보고서 | 포함 | - | 2026-01-28T17:54:02 | read-full | lines: 3; last: {"run_id": "05402154-2045-4d46-9d94-770b0af73950", "stage_id": "6b90d9bc-7bc0-4ba5-b60e-643621b135ac", "parent_stage_id" | JSONL lines=3 | 내부 |
| `./reports/r3_bm25_langfuse3_stage_events.jsonl` | JSONL | reports | lens:QA;type:보고서 | 포함 | - | 2026-01-28T17:54:02 | read-full | lines: 3; last: {"run_id": "3ab112c4-f0ae-447d-ab2e-1a4f30e2e114", "stage_id": "7abd4aab-abd4-4fe0-8750-58956a654a2e", "parent_stage_id" | JSONL lines=3 | 내부 |
| `./reports/r3_bm25_langfuse_stage_events.jsonl` | JSONL | reports | lens:QA;type:보고서 | 포함 | - | 2026-01-28T17:54:02 | read-full | lines: 3; last: {"run_id": "8226c563-3c0e-4ab9-bcd0-42fb855de656", "stage_id": "2b75e88a-2f58-476b-a11f-a3c4cd53fed3", "parent_stage_id" | JSONL lines=3 | 내부 |
| `./reports/r3_bm25_phoenix_stage_events.jsonl` | JSONL | reports | lens:QA;type:보고서 | 포함 | - | 2026-01-28T17:54:02 | read-full | lines: 3; last: {"run_id": "d82e84fe-9b56-4b28-bde6-dad0f031f99a", "stage_id": "92ac5ef5-daf3-459a-9adc-4670755ae2bb", "parent_stage_id" | JSONL lines=3 | 내부 |
| `./reports/r3_bm25_stage_events.jsonl` | JSONL | reports | lens:QA;type:보고서 | 포함 | - | 2026-01-28T17:54:02 | read-full | lines: 3; last: {"run_id": "3fd2f7e6-98ba-4d7b-9b1d-2760aade541d", "stage_id": "0c569939-1fcd-4487-9b79-baca9a243f1c", "parent_stage_id" | JSONL lines=3 | 내부 |
| `./reports/r3_bm25_stage_report.txt` | Text | reports | lens:QA;type:보고서 | 포함 | - | 2026-01-28T17:54:02 | read-full | last: └───────────┴──────────┴──────────────────────┴────────┴──────────────────────┘ | Text text file: r3_bm25_stage_report.txt | 내부 |
| `./reports/r3_dense_faiss_stage_events.jsonl` | JSONL | reports | lens:QA;type:보고서 | 포함 | - | 2026-01-28T17:54:02 | read-full | lines: 3; last: {"run_id": "r3-dense-faiss-1767506494", "stage_id": "fbcbd737-083b-437c-a7b4-5c59a2bdfbf3", "parent_stage_id": "205a6579 | JSONL lines=3 | 내부 |
| `./reports/r3_dense_faiss_stage_report.txt` | Text | reports | lens:QA;type:보고서 | 포함 | - | 2026-01-28T17:54:02 | read-full | last: └───────────┴───────────┴──────────────────────┴────────┴──────────────────────┘ | Text text file: r3_dense_faiss_stage_report.txt | 내부 |
| `./reports/ralph_loop_briefing.md` | Markdown | reports | lens:QA;type:보고서 | 포함 | - | 2026-01-28T17:54:02 | read-full | last: - 개발 에이전트 시스템: `agent/README.md` | Markdown text file: Ralph Loop 발표 사전 자료 (EvalVault 리포지토리 기반) | 내부 |
| `./reports/retrieval_benchmark_smoke_precision.csv` | CSV | reports | lens:QA;type:보고서 | 포함 | - | 2026-01-28T17:54:02 | read-full | lines: 4; last: hybrid,1.0,0.3333333333333333,1.0,1.0,2, | CSV lines=4 | 내부 |
| `./reports/retrieval_benchmark_smoke_precision_graphrag.csv` | CSV | reports | lens:QA;type:보고서 | 포함 | - | 2026-01-28T17:54:02 | read-full | lines: 5; last: graphrag,0.3333333333333333,1.0,1.0,1.0,2, | CSV lines=5 | 내부 |
| `./reports/retrieval_benchmark_smoke_precision_multi.csv` | CSV | reports | lens:QA;type:보고서 | 포함 | - | 2026-01-28T17:54:02 | read-full | lines: 4; last: hybrid,0.3333333333333333,1.0,1.0,1.0,2, | CSV lines=4 | 내부 |
| `./scratch/api.log` | LOG | misc | lens:제품;type:소스 | 포함 | - | 2026-01-28T17:54:02 | binary-scan | size: 813 bytes | LOG binary file (813 bytes) | 내부 |
| `./scratch/frontend.log` | LOG | misc | lens:제품;type:소스 | 포함 | - | 2026-01-28T17:54:02 | binary-scan | size: 257 bytes | LOG binary file (257 bytes) | 내부 |
| `./scratch/r1_smoke/dataset.json` | JSON | misc | lens:제품;type:소스 | 포함 | - | 2026-01-28T17:54:02 | read-full | keys: name,version,test_cases; last: } | JSON object with 3 keys | 내부 |
| `./scratch/r1_smoke/evalvault.db` | DB | misc | lens:제품;type:소스 | 포함 | - | 2026-01-28T17:54:02 | binary-scan | size: 159744 bytes | DB binary file (159744 bytes) | 내부 |
| `./scratch/r1_smoke/prompt.txt` | Text | misc | lens:제품;type:소스 | 포함 | - | 2026-01-28T17:54:02 | read-full | last: 당신은 보험 약관 QA를 돕는 도우미입니다. | Text text file: prompt.txt | 내부 |
| `./scratch/r1_smoke/prompt_manifest.json` | JSON | misc | lens:제품;type:소스 | 포함 | - | 2026-01-28T17:54:02 | read-full | keys: version,updated_at,prompts; last: } | JSON object with 3 keys | 내부 |
| `./scratch/r1_smoke/run.json` | JSON | misc | lens:제품;type:소스 | 포함 | - | 2026-01-28T17:54:02 | read-full | keys: run_id,dataset_name,dataset_version,model_name,started_at,finished_at,total_test_cases,passed_test_cases,pass_rate,total_tokens,total_cost_usd,duration_seconds; last: } | JSON object with 16 keys | 내부 |
| `./scratch/r1_smoke/run.log` | LOG | misc | lens:제품;type:소스 | 포함 | - | 2026-01-28T17:54:02 | binary-scan | size: 2834 bytes | LOG binary file (2834 bytes) | 내부 |
| `./scratch/r1_smoke/stage_events.jsonl` | JSONL | misc | lens:제품;type:소스 | 포함 | - | 2026-01-28T17:54:02 | read-full | lines: 4; last: {"run_id": "3dcb2b80-1744-4efd-837c-d7aea9348ebe", "stage_id": "08f67781-a128-4103-9abc-85d9af68f48b", "parent_stage_id" | JSONL lines=4 | 내부 |
| `./scratch/r1_smoke/stage_report.txt` | Text | misc | lens:제품;type:소스 | 포함 | - | 2026-01-28T17:54:02 | read-full | last: └───────────┴───────────┴──────────────────────┴────────┴──────────────────────┘ | Text text file: stage_report.txt | 내부 |
| `./scratch/ragrefine/__init__.py` | Python | misc | lens:제품;type:소스 | 포함 | - | 2026-01-28T17:54:02 | read-full | last: __version__ = "0.2.0" | Python text file: RAGRefine: Korean RAG evaluation analysis toolkit with Ollama LLM integration | 내부 |
| `./scratch/ragrefine/agent/__init__.py` | Python | misc | lens:제품;type:소스 | 포함 | - | 2026-01-28T17:54:02 | read-full | last: __all__ = \["get_agent", "chat"\] | Python text file: RAGRefine AI Agent Module | 내부 |
| `./scratch/ragrefine/agent/agent_manager.py` | Python | misc | lens:제품;type:소스 | 포함 | - | 2026-01-28T17:54:02 | read-full | last:     return manager.reset_agent(force=force) | Python text file: LangGraph       . | 내부 |
| `./scratch/ragrefine/agent/api.py` | Python | misc | lens:제품;type:소스 | 포함 | - | 2026-01-28T17:54:02 | read-full | last:     run_server() | Python text file: RAGRefine Agent API Server | 내부 |
| `./scratch/ragrefine/agent/cli.py` | Python | misc | lens:제품;type:소스 | 포함 | - | 2026-01-28T17:54:02 | read-full | last:     sys.exit(main()) | Python text file: RAGRefine Agent CLI | 내부 |
| `./scratch/ragrefine/agent/events.py` | Python | misc | lens:제품;type:소스 | 포함 | - | 2026-01-28T17:54:02 | read-full | last:     return event_class(**data) | Python text file: Event Schemas for RAGRefine Agent API | 내부 |
| `./scratch/ragrefine/agent/graph.py` | Python | misc | lens:제품;type:소스 | 포함 | - | 2026-01-28T17:54:02 | read-full | last:     } | Python text file: LangGraph State Graph for RAGRefine Agent | 내부 |
| `./scratch/ragrefine/agent/professional_prompts.py` | Python | misc | lens:제품;type:소스 | 포함 | - | 2026-01-28T17:54:02 | read-full | last: """ | Python text file: professional_prompts.py | 내부 |
| `./scratch/ragrefine/agent/session.py` | Python | misc | lens:제품;type:소스 | 포함 | - | 2026-01-28T17:54:02 | read-full | last:         return False | Python text file: Session Manager for RAGRefine Agent API | 내부 |
| `./scratch/ragrefine/agent/tools/__init__.py` | Python | misc | lens:제품;type:소스 | 포함 | - | 2026-01-28T17:54:02 | read-full | last:     return ANALYSIS_DATA_TOOLS | Python text file: RAGRefine Agent Tools | 내부 |
| `./scratch/ragrefine/agent/tools/advanced_smart_chat_tools.py` | Python | misc | lens:제품;type:소스 | 포함 | - | 2026-01-28T17:54:02 | read-full | last:     print(f" : {extracted}") | Python text file: Advanced Smart Chat Tools - RAGRefine 17      | 내부 |
| `./scratch/ragrefine/agent/tools/analysis_data_tools.py` | Python | misc | lens:제품;type:소스 | 포함 | - | 2026-01-28T17:54:02 | read-full | last: \] | Python text file: Analysis Data Loading Tools for RAGRefine Agent | 내부 |
| `./scratch/ragrefine/agent/tools/analysis_tools.py` | Python | misc | lens:제품;type:소스 | 포함 | - | 2026-01-28T17:54:02 | read-full | last: \] | Python text file: Analysis Tools for RAGRefine Agent | 내부 |
| `./scratch/ragrefine/agent/tools/auto_source_analyst.py` | Python | misc | lens:제품;type:소스 | 포함 | - | 2026-01-28T17:54:02 | read-full | last:             print(f"{intent.value}:  - {str(e)}") | Python text file: Auto Source Selection Analyst -      | 내부 |
| `./scratch/ragrefine/agent/tools/comparison_tools.py` | Python | misc | lens:제품;type:소스 | 포함 | - | 2026-01-28T17:54:02 | read-full | last: \] | Python text file: Comparison Tools for RAGRefine Agent | 내부 |
| `./scratch/ragrefine/agent/tools/file_tools.py` | Python | misc | lens:제품;type:소스 | 포함 | - | 2026-01-28T17:54:02 | read-full | last: \] | Python text file: File Tools for RAGRefine Agent | 내부 |
| `./scratch/ragrefine/agent/tools/lightweight_tools.py` | Python | misc | lens:제품;type:소스 | 포함 | - | 2026-01-28T17:54:02 | read-full | last: \] | Python text file: Lightweight Tools for RAGRefine Agent | 내부 |
| `./scratch/ragrefine/agent/tools/metadata.py` | Python | misc | lens:제품;type:소스 | 포함 | - | 2026-01-28T17:54:02 | read-full | last:     } | Python text file: Tool Metadata API for RAGRefine Agent | 내부 |
| `./scratch/ragrefine/agent/tools/multi_intent_analyst.py` | Python | misc | lens:제품;type:소스 | 포함 | - | 2026-01-28T17:54:02 | read-full | last:         print(f" : {result.required_tools}") | Python text file: Multi-Intent Analysis System -        | 내부 |
| `./scratch/ragrefine/agent/tools/simple_payload_reader.py` | Python | misc | lens:제품;type:소스 | 포함 | - | 2026-01-28T17:54:02 | read-full | last:         print("     .") | Python text file: Simple Payload Reader -  analysis_payload.json   | 내부 |
| `./scratch/ragrefine/agent/tools/smart_analyst_tools.py` | Python | misc | lens:제품;type:소스 | 포함 | - | 2026-01-28T17:54:02 | read-full | last:     print(result) | Python text file: Smart RAG Analyst Tools for Chat UI Integration | 내부 |
| `./scratch/ragrefine/agent/tools/smart_chat_tools.py` | Python | misc | lens:제품;type:소스 | 포함 | - | 2026-01-28T17:54:02 | read-full | last:         print("     .") | Python text file: Smart Chat UI Tools -      RAG  | 내부 |
| `./scratch/ragrefine/analysis/__init__.py` | Python | misc | lens:제품;type:소스 | 포함 | - | 2026-01-28T17:54:02 | read-full | last:     \]) | Python text file: RAGRefine Analysis Package | 내부 |
| `./scratch/ragrefine/analysis/advanced_ragas.py` | Python | misc | lens:제품;type:소스 | 포함 | - | 2026-01-28T17:54:02 | read-full | last:     return analyzer.analyze_from_file(file_path, output_dir, **kwargs) | Python text file: advanced_ragas.py | 내부 |
| `./scratch/ragrefine/analysis/bandit_optimizer.py` | Python | misc | lens:제품;type:소스 | 포함 | - | 2026-01-28T17:54:02 | read-full | last:         logger.info(f"Exported bandit result to {output_path}") | Python text file: bandit_optimizer.py | 내부 |
| `./scratch/ragrefine/analysis/bayesian_ab_test.py` | Python | misc | lens:제품;type:소스 | 포함 | - | 2026-01-28T17:54:02 | read-full | last:         logger.info(f"Exported Bayesian A/B results to {output_path}") | Python text file: bayesian_ab_test.py | 내부 |
| `./scratch/ragrefine/analysis/causal_analysis.py` | Python | misc | lens:제품;type:소스 | 포함 | - | 2026-01-28T17:54:02 | read-full | last:     return results | Python text file: RAGAS    ,    | 내부 |
| `./scratch/ragrefine/analysis/causal_reasoning_engine.py` | Python | misc | lens:제품;type:소스 | 포함 | - | 2026-01-28T17:54:02 | read-full | last:         return dag | Python text file: causal_reasoning_engine.py | 내부 |
| `./scratch/ragrefine/analysis/comprehensive_report_generator.py` | Python | misc | lens:제품;type:소스 | 포함 | - | 2026-01-28T17:54:02 | read-full | last:     main() | Python text file: RAGRefine      | 내부 |
| `./scratch/ragrefine/analysis/context_semantic_analyzer.py` | Python | misc | lens:제품;type:소스 | 포함 | - | 2026-01-28T17:54:02 | read-full | last:     return analyzer.analyze_all(df) | Python text file: context_semantic_analyzer.py | 내부 |
| `./scratch/ragrefine/analysis/data_pipeline.py` | Python | misc | lens:제품;type:소스 | 포함 | - | 2026-01-28T17:54:02 | read-full | last:     print("="*60 + "\n") | Python text file: RAGAS       | 내부 |
| `./scratch/ragrefine/analysis/dataset_profiler.py` | Python | misc | lens:제품;type:소스 | 포함 | - | 2026-01-28T17:54:02 | read-full | last:     return profiler.generate_profile(df, output_dir=output_dir, config=config) | Python text file: dataset_profiler.py | 내부 |
| `./scratch/ragrefine/analysis/deepeval_evaluator.py` | Python | misc | lens:제품;type:소스 | 포함 | - | 2026-01-28T17:54:02 | read-full | last:     return evaluator.evaluate_dataset(df) | Python text file: deepeval_evaluator.py | 내부 |
| `./scratch/ragrefine/analysis/diagnostic_playbook.py` | Python | misc | lens:제품;type:소스 | 포함 | - | 2026-01-28T17:54:02 | read-full | last:     print(f": {results\['summary'\]\['total_recommendations'\]}") | Python text file: diagnostic_playbook.py | 내부 |
| `./scratch/ragrefine/analysis/file_schema.py` | Python | misc | lens:제품;type:소스 | 포함 | - | 2026-01-28T17:54:02 | read-full | last:     return summary | Python text file: Analysis result schema references. | 내부 |
| `./scratch/ragrefine/analysis/hcx_client.py` | Python | misc | lens:제품;type:소스 | 포함 | - | 2026-01-28T17:54:02 | read-full | last:         return embeddings\[0\] if embeddings else \[\] | Python text file: HCX-005 API Client for RAGRefine | 내부 |
| `./scratch/ragrefine/analysis/io.py` | Python | misc | lens:제품;type:소스 | 포함 | - | 2026-01-28T17:54:02 | read-full | last:     return run_info | Python text file: RAGRefine | 내부 |
| `./scratch/ragrefine/analysis/keybert_analyzer.py` | Python | misc | lens:제품;type:소스 | 포함 | - | 2026-01-28T17:54:02 | read-full | last:     return results | Python text file: KeyBERT        | 내부 |
| `./scratch/ragrefine/analysis/llm_evaluation.py` | Python | misc | lens:제품;type:소스 | 포함 | - | 2026-01-28T17:54:02 | read-full | last:     return evaluator.evaluate_single(question, answer) | Python text file: Ollama  LLM   ( ) | 내부 |
| `./scratch/ragrefine/analysis/llm_service.py` | Python | misc | lens:제품;type:소스 | 포함 | - | 2026-01-28T17:54:02 | read-full | last:     return LLMService() | Python text file: Unified LLM Service Manager for RAGRefine | 내부 |
| `./scratch/ragrefine/analysis/locale_utils.py` | Python | misc | lens:제품;type:소스 | 포함 | - | 2026-01-28T17:54:02 | read-full | last:     return format_float(value, decimals=3, na_rep="-") | Python text file: locale_utils.py | 내부 |
| `./scratch/ragrefine/analysis/meta_analyzer.py` | Python | misc | lens:제품;type:소스 | 포함 | - | 2026-01-28T17:54:02 | read-full | last:         return report | Python text file: meta_analyzer.py | 내부 |
| `./scratch/ragrefine/analysis/meta_reviewer.py` | Python | misc | lens:제품;type:소스 | 포함 | - | 2026-01-28T17:54:02 | read-full | last:         logger.info(f"Exported meta review to {output_path}") | Python text file: meta_reviewer.py | 내부 |
| `./scratch/ragrefine/analysis/network_graph_analyzer.py` | Python | misc | lens:제품;type:소스 | 포함 | - | 2026-01-28T17:54:02 | read-full | last:     } | Python text file: network_graph_analyzer.py | 내부 |
| `./scratch/ragrefine/analysis/prompt_analysis.py` | Python | misc | lens:제품;type:소스 | 포함 | - | 2026-01-28T17:54:02 | read-full | last:     return comparison | Python text file: prompt_analysis.py | 내부 |
| `./scratch/ragrefine/analysis/question_analysis.py` | Python | misc | lens:제품;type:소스 | 포함 | - | 2026-01-28T17:54:02 | read-full | last:     return analyzer.analyze_questions(df) | Python text file: question_analysis.py | 내부 |
| `./scratch/ragrefine/analysis/question_type_classifier.py` | Python | misc | lens:제품;type:소스 | 포함 | - | 2026-01-28T17:54:02 | read-full | last:         \] | Python text file: question_type_classifier.py | 내부 |
| `./scratch/ragrefine/analysis/ragas_extensions.py` | Python | misc | lens:제품;type:소스 | 포함 | - | 2026-01-28T17:54:02 | read-full | last:     return evaluator.evaluate_single(question, answer) | Python text file: RAGAS    ( ) | 내부 |
| `./scratch/ragrefine/analysis/report/__init__.py` | Python | misc | lens:제품;type:소스 | 포함 | - | 2026-01-28T17:54:02 | read-full | last: \] | Python text file: __init__.py | 내부 |
| `./scratch/ragrefine/analysis/report/base_generator.py` | Python | misc | lens:제품;type:소스 | 포함 | - | 2026-01-28T17:54:02 | read-full | last:     return mapping.get(name, name) | Python text file: base_generator.py | 내부 |
| `./scratch/ragrefine/analysis/report_generator.py` | Python | misc | lens:제품;type:소스 | 포함 | - | 2026-01-28T17:54:02 | read-full | last:     return results | Python text file: report_generator.py | 내부 |
| `./scratch/ragrefine/analysis/report_graph.py` | Python | misc | lens:제품;type:소스 | 포함 | - | 2026-01-28T17:54:02 | read-full | last:         return fallback\[:25000\]  #  25,000 | Python text file: report_graph.py | 내부 |
| `./scratch/ragrefine/analysis/report_schema.py` | Python | misc | lens:제품;type:소스 | 포함 | - | 2026-01-28T17:54:02 | read-full | last:         } | Python text file: report_schema.py | 내부 |
| `./scratch/ragrefine/analysis/report_utils.py` | Python | misc | lens:제품;type:소스 | 포함 | - | 2026-01-28T17:54:02 | read-full | last:     return _convert(obj) | Python text file: report_utils.py | 내부 |
| `./scratch/ragrefine/analysis/result_loader.py` | Python | misc | lens:제품;type:소스 | 포함 | - | 2026-01-28T17:54:02 | read-full | last:     return results | Python text file: Analysis Result Loader | 내부 |
| `./scratch/ragrefine/analysis/temporal_analysis.py` | Python | misc | lens:제품;type:소스 | 포함 | - | 2026-01-28T17:54:02 | read-full | last:     return results | Python text file: RAGAS       ,  , | 내부 |
| `./scratch/ragrefine/analysis/topic_clustering.py` | Python | misc | lens:제품;type:소스 | 포함 | - | 2026-01-28T17:54:02 | read-full | last:     return results | Python text file: RAGAS    -  , | 내부 |
| `./scratch/ragrefine/analysis/types.py` | Python | misc | lens:제품;type:소스 | 포함 | - | 2026-01-28T17:54:02 | read-full | last:     confidence_level: float = 0.95 | Python text file: RAGRefine Analysis | 내부 |
| `./scratch/ragrefine/analysis/user_dictionary_analyzer.py` | Python | misc | lens:제품;type:소스 | 포함 | - | 2026-01-28T17:54:02 | read-full | last:         } | Python text file: User Dictionary Analysis Module for RAGRefine | 내부 |
| `./scratch/ragrefine/analysis/visualization.py` | Python | misc | lens:제품;type:소스 | 포함 | - | 2026-01-28T17:54:02 | read-full | last:     return visualizer.create_performance_distribution_plot(metrics_df) | Python text file: RAGAS     | 내부 |
| `./scratch/ragrefine/cache/__init__.py` | Python | misc | lens:제품;type:소스 | 포함 | - | 2026-01-28T17:54:02 | read-full | last: __all__ = \["AnalysisCache", "CacheConfig"\] | Python text file: RAGRefine | 내부 |
| `./scratch/ragrefine/cache/analysis_cache.py` | Python | misc | lens:제품;type:소스 | 포함 | - | 2026-01-28T17:54:02 | read-full | last:             logger.error(f"Error managing memory usage: {e}") | Python text file: Redis         . | 내부 |
| `./scratch/ragrefine/cache/cache_config.py` | Python | misc | lens:제품;type:소스 | 포함 | - | 2026-01-28T17:54:02 | read-full | last:         return self.max_value_size_mb * 1024 * 1024 | Python text file: Redis      . | 내부 |
| `./scratch/ragrefine/cli.py` | Python | misc | lens:제품;type:소스 | 포함 | - | 2026-01-28T17:54:02 | read-full | last:     sys.exit(main()) | Python text file: cli.py | 내부 |
| `./scratch/ragrefine/data/__init__.py` | Python | misc | lens:제품;type:소스 | 포함 | - | 2026-01-28T17:54:02 | read-full | last:     raise AttributeError(f"module {__name__!r} has no attribute {name!r}") | Python text file: RAGRefine Data Management Module | 내부 |
| `./scratch/ragrefine/data/quality_validator.py` | Python | misc | lens:제품;type:소스 | 포함 | - | 2026-01-28T17:54:02 | read-full | last:         return report | Python text file: quality_validator.py | 내부 |
| `./scratch/ragrefine/data/synthetic_data_engine.py` | Python | misc | lens:제품;type:소스 | 포함 | - | 2026-01-28T17:54:02 | read-full | last:         return df_synthetic | Python text file: synthetic_data_engine.py | 내부 |
| `./scratch/ragrefine/db/__init__.py` | Python | misc | lens:제품;type:소스 | 포함 | - | 2026-01-28T17:54:02 | read-full | last: __all__ = \["ChatHistoryDB"\] | Python text file: Database modules for RAGRefine. | 내부 |
| `./scratch/ragrefine/db/chat_history.py` | Python | misc | lens:제품;type:소스 | 포함 | - | 2026-01-28T17:54:02 | read-full | last:             conn.close() | Python text file: Chat History Database Module | 내부 |
| `./scratch/ragrefine/experiments/__init__.py` | Python | misc | lens:제품;type:소스 | 포함 | - | 2026-01-28T17:54:02 | read-full | last:     raise AttributeError(f"module {__name__!r} has no attribute {name!r}") | Python text file: RAGRefine Experiment Management Module | 내부 |
| `./scratch/ragrefine/experiments/comparison_engine.py` | Python | misc | lens:제품;type:소스 | 포함 | - | 2026-01-28T17:54:02 | read-full | last:     return df_ranks | Python text file: comparison_engine.py | 내부 |
| `./scratch/ragrefine/experiments/experiment_tracker.py` | Python | misc | lens:제품;type:소스 | 포함 | - | 2026-01-28T17:54:02 | read-full | last:         return \[e\['run_id'\] for e in sorted_exps\[:n\]\] | Python text file: experiment_tracker.py | 내부 |
| `./scratch/ragrefine/langgraph_report_generator.py` | Python | misc | lens:제품;type:소스 | 포함 | - | 2026-01-28T17:54:02 | read-full | last:     main() | Python text file: RAGRefine    (LangGraph ) | 내부 |
| `./scratch/ragrefine/logging_config.py` | Python | misc | lens:제품;type:소스 | 포함 | - | 2026-01-28T17:54:02 | read-full | last: __all__ = \["logger", "AnalysisMetrics", "LogTimer"\] | Python text file: Structured logging configuration for RAGRefine | 내부 |
| `./scratch/ragrefine/rag_expert_synth/__init__.py` | Python | misc | lens:제품;type:소스 | 포함 | - | 2026-01-28T17:54:02 | read-full | last: \] | Python text file: __init__.py | 내부 |
| `./scratch/ragrefine/rag_expert_synth/cli.py` | Python | misc | lens:제품;type:소스 | 포함 | - | 2026-01-28T17:54:02 | read-full | last:     return "\n".join(lines) | Python text file: cli.py | 내부 |
| `./scratch/ragrefine/rag_expert_synth/combiner.py` | Python | misc | lens:제품;type:소스 | 포함 | - | 2026-01-28T17:54:02 | read-full | last:     ) | Python text file: combiner.py | 내부 |
| `./scratch/ragrefine/rag_expert_synth/evidence.py` | Python | misc | lens:제품;type:소스 | 포함 | - | 2026-01-28T17:54:02 | read-full | last:         ev.weight *= context_coef | Python text file: evidence.py | 내부 |
| `./scratch/ragrefine/rag_expert_synth/exceptions.py` | Python | misc | lens:제품;type:소스 | 포함 | - | 2026-01-28T17:54:02 | read-full | last:         super().__init__(message, error_details) | Python text file: Custom exception hierarchy for rag_expert_synth. | 내부 |
| `./scratch/ragrefine/rag_expert_synth/fuzzy_rules.py` | Python | misc | lens:제품;type:소스 | 포함 | - | 2026-01-28T17:54:02 | read-full | last:     return directives | Python text file: () | 내부 |
| `./scratch/ragrefine/rag_expert_synth/renderer.py` | Python | misc | lens:제품;type:소스 | 포함 | - | 2026-01-28T17:54:02 | read-full | last:         return template.render(assessment=assessment_dict) | Python text file: renderer.py | 내부 |
| `./scratch/ragrefine/rag_expert_synth/rules.py` | Python | misc | lens:제품;type:소스 | 포함 | - | 2026-01-28T17:54:02 | read-full | last:     return recommend_actions(signals) | Python text file: rules.py | 내부 |
| `./scratch/ragrefine/rag_expert_synth/templates/base_report.md.j2` | J2 | misc | lens:제품;type:소스 | 포함 | - | 2026-01-28T17:54:02 | binary-scan | size: 1159 bytes | J2 binary file (1159 bytes) | 내부 |
| `./scratch/ragrefine/rag_expert_synth/types.py` | Python | misc | lens:제품;type:소스 | 포함 | - | 2026-01-28T17:54:02 | read-full | last:     model_config = {"frozen": True} | Python text file: types.py | 내부 |
| `./scratch/ragrefine/utils/chat_data_reader.py` | Python | misc | lens:제품;type:소스 | 포함 | - | 2026-01-28T17:54:02 | read-full | last:     main() | Python text file: chat_data_reader.py | 내부 |
| `./scratch/ragrefine/utils/chat_insights_generator.py` | Python | misc | lens:제품;type:소스 | 포함 | - | 2026-01-28T17:54:02 | read-full | last:         return False | Python text file: chat_insights_generator.py | 내부 |
| `./scratch/ragrefine/utils/intelligent_data_retriever.py` | Python | misc | lens:제품;type:소스 | 포함 | - | 2026-01-28T17:54:02 | read-full | last:     asyncio.run(main()) | Python text file: intelligent_data_retriever.py | 내부 |
| `./scratch/summary_eval_smoke_2.json` | JSON | misc | lens:제품;type:소스 | 포함 | - | 2026-01-28T17:54:02 | read-full | keys: name,version,description,thresholds,test_cases; last: } | JSON object with 5 keys | 내부 |
| `./scratch/summary_eval_smoke_3.json` | JSON | misc | lens:제품;type:소스 | 포함 | - | 2026-01-28T17:54:02 | read-full | keys: name,version,description,thresholds,test_cases; last: } | JSON object with 5 keys | 내부 |
| `./scratch/summary_eval_smoke_3_insurance.json` | JSON | misc | lens:제품;type:소스 | 포함 | - | 2026-01-28T17:54:02 | read-full | keys: name,version,description,thresholds,test_cases,metadata; last: } | JSON object with 6 keys | 내부 |
| `./scripts/benchmark/download_kmmlu.py` | Python | scripts | lens:개발;type:소스 | 포함 | - | 2026-01-28T17:54:02 | read-full | last:     main() | Python text file: download_kmmlu.py | 내부 |
| `./scripts/ci/run_regression_gate.py` | Python | scripts | lens:개발;type:소스 | 포함 | - | 2026-01-28T17:54:02 | read-full | last:     raise SystemExit(main()) | Python text file: Run regression suites for CI quality gate. | 내부 |
| `./scripts/dev/open_rag_trace_demo.py` | Python | scripts | lens:개발;type:소스 | 포함 | - | 2026-01-28T17:54:02 | read-full | last:     raise SystemExit(main()) | Python text file: open_rag_trace_demo.py | 내부 |
| `./scripts/dev/open_rag_trace_integration_template.py` | Python | scripts | lens:개발;type:소스 | 포함 | - | 2026-01-28T17:54:02 | read-full | last: \] | Python text file: open_rag_trace_integration_template.py | 내부 |
| `./scripts/dev/otel-collector-config.yaml` | YAML | scripts | lens:개발;type:소스 | 포함 | - | 2026-01-28T17:54:02 | read-full | last:       exporters: \[otlphttp/phoenix\] | YAML text file: otel-collector-config.yaml | 내부 |
| `./scripts/dev/start_web_ui_with_phoenix.sh` | SH | scripts | lens:개발;type:소스 | 포함 | - | 2026-01-28T17:54:02 | binary-scan | size: 3261 bytes | SH binary file (3261 bytes) | 내부 |
| `./scripts/dev/validate_open_rag_trace.py` | Python | scripts | lens:개발;type:소스 | 포함 | - | 2026-01-28T17:54:02 | read-full | last:     raise SystemExit(main()) | Python text file: validate_open_rag_trace.py | 내부 |
| `./scripts/dev/verify_dashboard_endpoint.sh` | SH | scripts | lens:개발;type:소스 | 포함 | - | 2026-01-28T17:54:02 | binary-scan | size: 1962 bytes | SH binary file (1962 bytes) | 내부 |
| `./scripts/dev_seed_pipeline_results.py` | Python | scripts | lens:개발;type:소스 | 포함 | - | 2026-01-28T17:54:02 | read-full | last:     main() | Python text file: Seed pipeline_results with sample data for UI comparison demos. | 내부 |
| `./scripts/docs/__init__.py` | Python | scripts | lens:개발;type:소스 | 포함 | - | 2026-01-28T17:54:02 | read-full | last: """ | Python text file: API documentation generation utilities. | 내부 |
| `./scripts/docs/analyzer/__init__.py` | Python | scripts | lens:개발;type:소스 | 포함 | - | 2026-01-28T17:54:02 | read-full | last: \] | Python text file: Code analysis modules. | 내부 |
| `./scripts/docs/analyzer/ast_scanner.py` | Python | scripts | lens:개발;type:소스 | 포함 | - | 2026-01-28T17:54:02 | read-full | last:             return "<unparseable>" | Python text file: AST-based Python source code scanner. | 내부 |
| `./scripts/docs/analyzer/confidence_scorer.py` | Python | scripts | lens:개발;type:소스 | 포함 | - | 2026-01-28T17:54:02 | read-full | last:                         param.description = match.group(3).strip() | Python text file: Confidence scoring for type information. | 내부 |
| `./scripts/docs/analyzer/graph_builder.py` | Python | scripts | lens:개발;type:소스 | 포함 | - | 2026-01-28T17:54:02 | read-full | last:             t *= 0.95 | Python text file: Graph builder for type and dependency visualization. | 내부 |
| `./scripts/docs/analyzer/side_effect_detector.py` | Python | scripts | lens:개발;type:소스 | 포함 | - | 2026-01-28T17:54:02 | read-full | last:         return unique | Python text file: Side effect detection for Python code. | 내부 |
| `./scripts/docs/generate_api_docs.py` | Python | scripts | lens:개발;type:소스 | 포함 | - | 2026-01-28T17:54:02 | read-full | last:     main() | Python text file: generate_api_docs.py | 내부 |
| `./scripts/docs/models/__init__.py` | Python | scripts | lens:개발;type:소스 | 포함 | - | 2026-01-28T17:54:02 | read-full | last: \] | Python text file: Data models for API documentation. | 내부 |
| `./scripts/docs/models/schema.py` | Python | scripts | lens:개발;type:소스 | 포함 | - | 2026-01-28T17:54:02 | read-full | last:     statistics: dict = field(default_factory=dict) | Python text file: Data models for code analysis and documentation. | 내부 |
| `./scripts/docs/renderer/__init__.py` | Python | scripts | lens:개발;type:소스 | 포함 | - | 2026-01-28T17:54:02 | read-full | last: __all__ = \["HTMLGenerator"\] | Python text file: Report rendering modules. | 내부 |
| `./scripts/docs/renderer/html_generator.py` | Python | scripts | lens:개발;type:소스 | 포함 | - | 2026-01-28T17:54:02 | read-full | last:         path.write_text(js, encoding="utf-8") | Python text file: Interactive HTML report generator. | 내부 |
| `./scripts/offline/bundle_datasets.sh` | SH | scripts | lens:개발;type:소스 | 포함 | - | 2026-01-28T17:54:02 | binary-scan | size: 841 bytes | SH binary file (841 bytes) | 내부 |
| `./scripts/offline/export_images.sh` | SH | scripts | lens:개발;type:소스 | 포함 | - | 2026-01-28T17:54:02 | binary-scan | size: 594 bytes | SH binary file (594 bytes) | 내부 |
| `./scripts/offline/import_images.sh` | SH | scripts | lens:개발;type:소스 | 포함 | - | 2026-01-28T17:54:02 | binary-scan | size: 289 bytes | SH binary file (289 bytes) | 내부 |
| `./scripts/offline/restore_datasets.sh` | SH | scripts | lens:개발;type:소스 | 포함 | - | 2026-01-28T17:54:02 | binary-scan | size: 304 bytes | SH binary file (304 bytes) | 내부 |
| `./scripts/offline/smoke_test.sh` | SH | scripts | lens:개발;type:소스 | 포함 | - | 2026-01-28T17:54:02 | binary-scan | size: 356 bytes | SH binary file (356 bytes) | 내부 |
| `./scripts/ops/phoenix_watch.py` | Python | scripts | lens:개발;type:소스 | 포함 | - | 2026-01-28T17:54:02 | read-full | last:     main() | Python text file: phoenix_watch.py | 내부 |
| `./scripts/perf/backfill_langfuse_trace_url.py` | Python | scripts | lens:개발;type:소스 | 포함 | - | 2026-01-28T17:54:02 | read-full | last:     raise SystemExit(main()) | Python text file: Backfill Langfuse trace_url into evaluation_runs metadata. | 내부 |
| `./scripts/perf/r3_dense_smoke.py` | Python | scripts | lens:개발;type:소스 | 포함 | - | 2026-01-28T17:54:02 | read-full | last:     main() | Python text file: R3 dense retriever performance smoke test. | 내부 |
| `./scripts/perf/r3_evalvault_run_dataset.json` | JSON | scripts | lens:개발;type:소스 | 포함 | - | 2026-01-28T17:54:02 | read-full | keys: name,version,description,test_cases; last: } | JSON object with 4 keys | 내부 |
| `./scripts/perf/r3_retriever_docs.json` | JSON | scripts | lens:개발;type:소스 | 포함 | - | 2026-01-28T17:54:02 | read-full | keys: documents; last: } | JSON object with 1 keys | 내부 |
| `./scripts/perf/r3_smoke_real.jsonl` | JSONL | scripts | lens:개발;type:소스 | 포함 | - | 2026-01-28T17:54:02 | read-full | lines: 6; last: {"event": "r3.smoke.summary", "ts": 1767502134.513189, "run_id": "r3-smoke-1767502115", "documents": 1000, "queries": 20 | JSONL lines=6 | 내부 |
| `./scripts/perf/r3_stage_events_sample.jsonl` | JSONL | scripts | lens:개발;type:소스 | 포함 | - | 2026-01-28T17:54:02 | read-full | lines: 4; last: {"run_id": "r3-smoke-1767502115", "stage_id": "6d78e311-2c80-4d9b-a498-fd9d5b56ee2f", "parent_stage_id": "857d8b29-8646- | JSONL lines=4 | 내부 |
| `./scripts/pipeline_template_inspect.py` | Python | scripts | lens:개발;type:소스 | 포함 | - | 2026-01-28T17:54:02 | read-full | last:     main() | Python text file: pipeline_template_inspect.py | 내부 |
| `./scripts/reports/generate_release_notes.py` | Python | scripts | lens:개발;type:소스 | 포함 | - | 2026-01-28T17:54:02 | read-full | last:     main() | Python text file: generate_release_notes.py | 내부 |
| `./scripts/run_with_timeout.py` | Python | scripts | lens:개발;type:소스 | 포함 | - | 2026-01-28T17:54:02 | read-full | last:     main() | Python text file: run_with_timeout.py | 내부 |
| `./scripts/test_full_evaluation.py` | Python | scripts | lens:개발;type:소스 | 포함 | - | 2026-01-28T17:54:02 | read-full | last:     print(f"\nResult Summary: {json.dumps(result, indent=2, default=str)}") | Python text file: test_full_evaluation.py | 내부 |
| `./scripts/tests/run_regressions.py` | Python | scripts | lens:개발;type:소스 | 포함 | - | 2026-01-28T17:54:02 | read-full | last:     raise SystemExit(main()) | Python text file: run_regressions.py | 내부 |
| `./scripts/tests/run_retriever_stage_report_smoke.sh` | SH | scripts | lens:개발;type:소스 | 포함 | - | 2026-01-28T17:54:02 | binary-scan | size: 2876 bytes | SH binary file (2876 bytes) | 내부 |
| `./scripts/validate_tutorials.py` | Python | scripts | lens:개발;type:소스 | 포함 | - | 2026-01-28T17:54:02 | read-full | last:     main() | Python text file: validate_tutorials.py | 내부 |
| `./scripts/verify_ragas_compliance.py` | Python | scripts | lens:개발;type:소스 | 포함 | - | 2026-01-28T17:55:07 | read-full | last:     sys.exit(exit_code) | Python text file: verify_ragas_compliance.py | 내부 |
| `./scripts/verify_workflows.py` | Python | scripts | lens:개발;type:소스 | 포함 | - | 2026-01-28T17:55:07 | read-full | last:     raise SystemExit(main()) | Python text file: Helper script to orchestrate integration and end-to-end checks. | 내부 |
| `./site/404.html` | HTML | misc | lens:제품;type:소스 | 포함 | - | 2026-01-28T17:55:07 | read-full | last: </html> | HTML text file: 404.html | 내부 |
| `./site/ANALYSIS_IMPROVEMENT_PLAN/index.html` | HTML | misc | lens:제품;type:소스 | 포함 | - | 2026-01-28T17:55:07 | read-full | last: </html> | HTML text file: index.html | 내부 |
| `./site/INDEX/index.html` | HTML | misc | lens:제품;type:소스 | 포함 | - | 2026-01-28T17:55:07 | read-full | last: </html> | HTML text file: index.html | 내부 |
| `./site/README.ko/index.html` | HTML | misc | lens:제품;type:소스 | 포함 | - | 2026-01-28T17:55:07 | read-full | last: </html> | HTML text file: index.html | 내부 |
| `./site/ROADMAP/index.html` | HTML | misc | lens:제품;type:소스 | 포함 | - | 2026-01-28T17:55:07 | read-full | last: </html> | HTML text file: index.html | 내부 |
| `./site/STATUS/index.html` | HTML | misc | lens:제품;type:소스 | 포함 | - | 2026-01-28T17:55:07 | read-full | last: </html> | HTML text file: index.html | 내부 |
| `./site/api/adapters/inbound/index.html` | HTML | misc | lens:제품;type:소스 | 포함 | - | 2026-01-28T17:55:07 | read-full | last: </html> | HTML text file: index.html | 내부 |
| `./site/api/adapters/outbound/index.html` | HTML | misc | lens:제품;type:소스 | 포함 | - | 2026-01-28T17:55:07 | read-full | last: </html> | HTML text file: index.html | 내부 |
| `./site/api/config/index.html` | HTML | misc | lens:제품;type:소스 | 포함 | - | 2026-01-28T17:55:07 | read-full | last: </html> | HTML text file: index.html | 내부 |
| `./site/api/domain/entities/index.html` | HTML | misc | lens:제품;type:소스 | 포함 | - | 2026-01-28T17:55:07 | read-full | last: </html> | HTML text file: index.html | 내부 |
| `./site/api/domain/metrics/index.html` | HTML | misc | lens:제품;type:소스 | 포함 | - | 2026-01-28T17:55:07 | read-full | last: </html> | HTML text file: index.html | 내부 |
| `./site/api/domain/services/index.html` | HTML | misc | lens:제품;type:소스 | 포함 | - | 2026-01-28T17:55:07 | read-full | last: </html> | HTML text file: index.html | 내부 |
| `./site/api/ports/inbound/index.html` | HTML | misc | lens:제품;type:소스 | 포함 | - | 2026-01-28T17:55:07 | read-full | last: </html> | HTML text file: index.html | 내부 |
| `./site/api/ports/outbound/index.html` | HTML | misc | lens:제품;type:소스 | 포함 | - | 2026-01-28T17:55:07 | read-full | last: </html> | HTML text file: index.html | 내부 |
| `./site/architecture/open-rag-trace-collector/index.html` | HTML | misc | lens:제품;type:소스 | 포함 | - | 2026-01-28T17:55:07 | read-full | last: </html> | HTML text file: index.html | 내부 |
| `./site/architecture/open-rag-trace-spec/index.html` | HTML | misc | lens:제품;type:소스 | 포함 | - | 2026-01-28T17:55:07 | read-full | last: </html> | HTML text file: index.html | 내부 |
| `./site/assets/_mkdocstrings.css` | CSS | misc | lens:제품;type:소스 | 포함 | - | 2026-01-28T17:55:07 | read-full | last: } | CSS text file: _mkdocstrings.css | 내부 |
| `./site/assets/images/favicon.png` | PNG | misc | lens:제품;type:소스 | 포함 | - | 2026-01-28T17:55:07 | read-full | size: 1870 bytes; dim: 48x48 | Image 48x48 | 내부 |
| `./site/assets/javascripts/bundle.79ae519e.min.js` | JavaScript | misc | lens:제품;type:소스 | 포함 | - | 2026-01-28T17:55:07 | read-full | last: //# sourceMappingURL=bundle.79ae519e.min.js.map | JavaScript text file: bundle.79ae519e.min.js | 내부 |
| `./site/assets/javascripts/bundle.79ae519e.min.js.map` | MAP | misc | lens:제품;type:소스 | 포함 | - | 2026-01-28T17:55:07 | binary-scan | size: 1026989 bytes | MAP binary file (1026989 bytes) | 내부 |
| `./site/assets/javascripts/lunr/min/lunr.ar.min.js` | JavaScript | misc | lens:제품;type:소스 | 포함 | - | 2026-01-28T17:55:07 | read-full | last: !function(e,r){"function"==typeof define&&define.amd?define(r):"object"==typeof exports?module.exports=r():r()(e.lunr)}( | JavaScript text file: lunr.ar.min.js | 내부 |
| `./site/assets/javascripts/lunr/min/lunr.da.min.js` | JavaScript | misc | lens:제품;type:소스 | 포함 | - | 2026-01-28T17:55:07 | read-full | last: !function(e,r){"function"==typeof define&&define.amd?define(r):"object"==typeof exports?module.exports=r():r()(e.lunr)}( | JavaScript text file: lunr.da.min.js | 내부 |
| `./site/assets/javascripts/lunr/min/lunr.de.min.js` | JavaScript | misc | lens:제품;type:소스 | 포함 | - | 2026-01-28T17:55:07 | read-full | last: !function(e,r){"function"==typeof define&&define.amd?define(r):"object"==typeof exports?module.exports=r():r()(e.lunr)}( | JavaScript text file: lunr.de.min.js | 내부 |
| `./site/assets/javascripts/lunr/min/lunr.du.min.js` | JavaScript | misc | lens:제품;type:소스 | 포함 | - | 2026-01-28T17:55:07 | read-full | last: !function(e,r){"function"==typeof define&&define.amd?define(r):"object"==typeof exports?module.exports=r():r()(e.lunr)}( | JavaScript text file: lunr.du.min.js | 내부 |
| `./site/assets/javascripts/lunr/min/lunr.el.min.js` | JavaScript | misc | lens:제품;type:소스 | 포함 | - | 2026-01-28T17:55:07 | read-full | last: !function(e,t){"function"==typeof define&&define.amd?define(t):"object"==typeof exports?module.exports=t():t()(e.lunr)}( | JavaScript text file: lunr.el.min.js | 내부 |
| `./site/assets/javascripts/lunr/min/lunr.es.min.js` | JavaScript | misc | lens:제품;type:소스 | 포함 | - | 2026-01-28T17:55:07 | read-full | last: !function(e,s){"function"==typeof define&&define.amd?define(s):"object"==typeof exports?module.exports=s():s()(e.lunr)}( | JavaScript text file: lunr.es.min.js | 내부 |
| `./site/assets/javascripts/lunr/min/lunr.fi.min.js` | JavaScript | misc | lens:제품;type:소스 | 포함 | - | 2026-01-28T17:55:07 | read-full | last: !function(i,e){"function"==typeof define&&define.amd?define(e):"object"==typeof exports?module.exports=e():e()(i.lunr)}( | JavaScript text file: lunr.fi.min.js | 내부 |
| `./site/assets/javascripts/lunr/min/lunr.fr.min.js` | JavaScript | misc | lens:제품;type:소스 | 포함 | - | 2026-01-28T17:55:07 | read-full | last: !function(e,r){"function"==typeof define&&define.amd?define(r):"object"==typeof exports?module.exports=r():r()(e.lunr)}( | JavaScript text file: lunr.fr.min.js | 내부 |
| `./site/assets/javascripts/lunr/min/lunr.he.min.js` | JavaScript | misc | lens:제품;type:소스 | 포함 | - | 2026-01-28T17:55:07 | read-full | last: !function(e,r){"function"==typeof define&&define.amd?define(r):"object"==typeof exports?module.exports=r():r()(e.lunr)}( | JavaScript text file: lunr.he.min.js | 내부 |
| `./site/assets/javascripts/lunr/min/lunr.hi.min.js` | JavaScript | misc | lens:제품;type:소스 | 포함 | - | 2026-01-28T17:55:07 | read-full | last: !function(e,r){"function"==typeof define&&define.amd?define(r):"object"==typeof exports?module.exports=r():r()(e.lunr)}( | JavaScript text file: lunr.hi.min.js | 내부 |
| `./site/assets/javascripts/lunr/min/lunr.hu.min.js` | JavaScript | misc | lens:제품;type:소스 | 포함 | - | 2026-01-28T17:55:07 | read-full | last: !function(e,n){"function"==typeof define&&define.amd?define(n):"object"==typeof exports?module.exports=n():n()(e.lunr)}( | JavaScript text file: lunr.hu.min.js | 내부 |
| `./site/assets/javascripts/lunr/min/lunr.hy.min.js` | JavaScript | misc | lens:제품;type:소스 | 포함 | - | 2026-01-28T17:55:07 | read-full | last: !function(e,r){"function"==typeof define&&define.amd?define(r):"object"==typeof exports?module.exports=r():r()(e.lunr)}( | JavaScript text file: lunr.hy.min.js | 내부 |
| `./site/assets/javascripts/lunr/min/lunr.it.min.js` | JavaScript | misc | lens:제품;type:소스 | 포함 | - | 2026-01-28T17:55:07 | read-full | last: !function(e,r){"function"==typeof define&&define.amd?define(r):"object"==typeof exports?module.exports=r():r()(e.lunr)}( | JavaScript text file: lunr.it.min.js | 내부 |
| `./site/assets/javascripts/lunr/min/lunr.ja.min.js` | JavaScript | misc | lens:제품;type:소스 | 포함 | - | 2026-01-28T17:55:07 | read-full | last: !function(e,r){"function"==typeof define&&define.amd?define(r):"object"==typeof exports?module.exports=r():r()(e.lunr)}( | JavaScript text file: lunr.ja.min.js | 내부 |
| `./site/assets/javascripts/lunr/min/lunr.jp.min.js` | JavaScript | misc | lens:제품;type:소스 | 포함 | - | 2026-01-28T17:55:07 | read-full | last: module.exports=require("./lunr.ja"); | JavaScript text file: lunr.jp.min.js | 내부 |
| `./site/assets/javascripts/lunr/min/lunr.kn.min.js` | JavaScript | misc | lens:제품;type:소스 | 포함 | - | 2026-01-28T17:55:07 | read-full | last: !function(e,r){"function"==typeof define&&define.amd?define(r):"object"==typeof exports?module.exports=r():r()(e.lunr)}( | JavaScript text file: lunr.kn.min.js | 내부 |
| `./site/assets/javascripts/lunr/min/lunr.ko.min.js` | JavaScript | misc | lens:제품;type:소스 | 포함 | - | 2026-01-28T17:55:07 | read-full | last: !function(e,r){"function"==typeof define&&define.amd?define(r):"object"==typeof exports?module.exports=r():r()(e.lunr)}( | JavaScript text file: lunr.ko.min.js | 내부 |
| `./site/assets/javascripts/lunr/min/lunr.multi.min.js` | JavaScript | misc | lens:제품;type:소스 | 포함 | - | 2026-01-28T17:55:07 | read-full | last: !function(e,t){"function"==typeof define&&define.amd?define(t):"object"==typeof exports?module.exports=t():t()(e.lunr)}( | JavaScript text file: lunr.multi.min.js | 내부 |
| `./site/assets/javascripts/lunr/min/lunr.nl.min.js` | JavaScript | misc | lens:제품;type:소스 | 포함 | - | 2026-01-28T17:55:07 | read-full | last: !function(r,e){"function"==typeof define&&define.amd?define(e):"object"==typeof exports?module.exports=e():e()(r.lunr)}( | JavaScript text file: lunr.nl.min.js | 내부 |
| `./site/assets/javascripts/lunr/min/lunr.no.min.js` | JavaScript | misc | lens:제품;type:소스 | 포함 | - | 2026-01-28T17:55:07 | read-full | last: !function(e,r){"function"==typeof define&&define.amd?define(r):"object"==typeof exports?module.exports=r():r()(e.lunr)}( | JavaScript text file: lunr.no.min.js | 내부 |
| `./site/assets/javascripts/lunr/min/lunr.pt.min.js` | JavaScript | misc | lens:제품;type:소스 | 포함 | - | 2026-01-28T17:55:07 | read-full | last: !function(e,r){"function"==typeof define&&define.amd?define(r):"object"==typeof exports?module.exports=r():r()(e.lunr)}( | JavaScript text file: lunr.pt.min.js | 내부 |
| `./site/assets/javascripts/lunr/min/lunr.ro.min.js` | JavaScript | misc | lens:제품;type:소스 | 포함 | - | 2026-01-28T17:55:07 | read-full | last: !function(e,i){"function"==typeof define&&define.amd?define(i):"object"==typeof exports?module.exports=i():i()(e.lunr)}( | JavaScript text file: lunr.ro.min.js | 내부 |
| `./site/assets/javascripts/lunr/min/lunr.ru.min.js` | JavaScript | misc | lens:제품;type:소스 | 포함 | - | 2026-01-28T17:55:07 | read-full | last: !function(e,n){"function"==typeof define&&define.amd?define(n):"object"==typeof exports?module.exports=n():n()(e.lunr)}( | JavaScript text file: lunr.ru.min.js | 내부 |
| `./site/assets/javascripts/lunr/min/lunr.sa.min.js` | JavaScript | misc | lens:제품;type:소스 | 포함 | - | 2026-01-28T17:55:07 | read-full | last: !function(e,r){"function"==typeof define&&define.amd?define(r):"object"==typeof exports?module.exports=r():r()(e.lunr)}( | JavaScript text file: lunr.sa.min.js | 내부 |
| `./site/assets/javascripts/lunr/min/lunr.stemmer.support.min.js` | JavaScript | misc | lens:제품;type:소스 | 포함 | - | 2026-01-28T17:55:07 | read-full | last: !function(r,t){"function"==typeof define&&define.amd?define(t):"object"==typeof exports?module.exports=t():t()(r.lunr)}( | JavaScript text file: lunr.stemmer.support.min.js | 내부 |
| `./site/assets/javascripts/lunr/min/lunr.sv.min.js` | JavaScript | misc | lens:제품;type:소스 | 포함 | - | 2026-01-28T17:55:07 | read-full | last: !function(e,r){"function"==typeof define&&define.amd?define(r):"object"==typeof exports?module.exports=r():r()(e.lunr)}( | JavaScript text file: lunr.sv.min.js | 내부 |
| `./site/assets/javascripts/lunr/min/lunr.ta.min.js` | JavaScript | misc | lens:제품;type:소스 | 포함 | - | 2026-01-28T17:55:07 | read-full | last: !function(e,t){"function"==typeof define&&define.amd?define(t):"object"==typeof exports?module.exports=t():t()(e.lunr)}( | JavaScript text file: lunr.ta.min.js | 내부 |
| `./site/assets/javascripts/lunr/min/lunr.te.min.js` | JavaScript | misc | lens:제품;type:소스 | 포함 | - | 2026-01-28T17:55:07 | read-full | last: !function(e,t){"function"==typeof define&&define.amd?define(t):"object"==typeof exports?module.exports=t():t()(e.lunr)}( | JavaScript text file: lunr.te.min.js | 내부 |
| `./site/assets/javascripts/lunr/min/lunr.th.min.js` | JavaScript | misc | lens:제품;type:소스 | 포함 | - | 2026-01-28T17:55:07 | read-full | last: !function(e,r){"function"==typeof define&&define.amd?define(r):"object"==typeof exports?module.exports=r():r()(e.lunr)}( | JavaScript text file: lunr.th.min.js | 내부 |
| `./site/assets/javascripts/lunr/min/lunr.tr.min.js` | JavaScript | misc | lens:제품;type:소스 | 포함 | - | 2026-01-28T17:55:07 | read-full | last: !function(r,i){"function"==typeof define&&define.amd?define(i):"object"==typeof exports?module.exports=i():i()(r.lunr)}( | JavaScript text file: lunr.tr.min.js | 내부 |
| `./site/assets/javascripts/lunr/min/lunr.vi.min.js` | JavaScript | misc | lens:제품;type:소스 | 포함 | - | 2026-01-28T17:55:07 | read-full | last: !function(e,r){"function"==typeof define&&define.amd?define(r):"object"==typeof exports?module.exports=r():r()(e.lunr)}( | JavaScript text file: lunr.vi.min.js | 내부 |
| `./site/assets/javascripts/lunr/min/lunr.zh.min.js` | JavaScript | misc | lens:제품;type:소스 | 포함 | - | 2026-01-28T17:55:07 | read-full | last: !function(e,r){"function"==typeof define&&define.amd?define(r):"object"==typeof exports?module.exports=r(require("@node- | JavaScript text file: lunr.zh.min.js | 내부 |
| `./site/assets/javascripts/lunr/tinyseg.js` | JavaScript | misc | lens:제품;type:소스 | 포함 | - | 2026-01-28T17:55:07 | read-full | last: })); | JavaScript text file: tinyseg.js | 내부 |
| `./site/assets/javascripts/lunr/wordcut.js` | JavaScript | misc | lens:제품;type:소스 | 포함 | - | 2026-01-28T17:55:07 | read-full | last: }); | JavaScript text file: wordcut.js | 내부 |
| `./site/assets/javascripts/workers/search.2c215733.min.js` | JavaScript | misc | lens:제품;type:소스 | 포함 | - | 2026-01-28T17:55:07 | read-full | last: //# sourceMappingURL=search.2c215733.min.js.map | JavaScript text file: search.2c215733.min.js | 내부 |
| `./site/assets/javascripts/workers/search.2c215733.min.js.map` | MAP | misc | lens:제품;type:소스 | 포함 | - | 2026-01-28T17:55:07 | binary-scan | size: 216029 bytes | MAP binary file (216029 bytes) | 내부 |
| `./site/assets/stylesheets/main.484c7ddc.min.css` | CSS | misc | lens:제품;type:소스 | 포함 | - | 2026-01-28T17:55:07 | read-full | last: @charset "UTF-8";html{-webkit-text-size-adjust:none;-moz-text-size-adjust:none;text-size-adjust:none;box-sizing:border-b | CSS text file: main.484c7ddc.min.css | 내부 |
| `./site/assets/stylesheets/main.484c7ddc.min.css.map` | MAP | misc | lens:제품;type:소스 | 포함 | - | 2026-01-28T17:55:07 | binary-scan | size: 47588 bytes | MAP binary file (47588 bytes) | 내부 |
| `./site/assets/stylesheets/palette.ab4e12ef.min.css` | CSS | misc | lens:제품;type:소스 | 포함 | - | 2026-01-28T17:55:07 | read-full | last: @media screen{\[data-md-color-scheme=slate\]{--md-default-fg-color:hsla(var(--md-hue),15%,90%,0.82);--md-default-fg-color- | CSS text file: palette.ab4e12ef.min.css | 내부 |
| `./site/assets/stylesheets/palette.ab4e12ef.min.css.map` | MAP | misc | lens:제품;type:소스 | 포함 | - | 2026-01-28T17:55:07 | binary-scan | size: 3670 bytes | MAP binary file (3670 bytes) | 내부 |
| `./site/getting-started/INSTALLATION/index.html` | HTML | misc | lens:제품;type:소스 | 포함 | - | 2026-01-28T17:55:07 | read-full | last: </html> | HTML text file: index.html | 내부 |
| `./site/guides/DEV_GUIDE/index.html` | HTML | misc | lens:제품;type:소스 | 포함 | - | 2026-01-28T17:55:07 | read-full | last: </html> | HTML text file: index.html | 내부 |
| `./site/guides/RELEASE_CHECKLIST/index.html` | HTML | misc | lens:제품;type:소스 | 포함 | - | 2026-01-28T17:55:07 | read-full | last: </html> | HTML text file: index.html | 내부 |
| `./site/guides/USER_GUIDE/index.html` | HTML | misc | lens:제품;type:소스 | 포함 | - | 2026-01-28T17:55:07 | read-full | last: </html> | HTML text file: index.html | 내부 |
| `./site/guides/open-rag-trace-internal-adapter/index.html` | HTML | misc | lens:제품;type:소스 | 포함 | - | 2026-01-28T17:55:07 | read-full | last: </html> | HTML text file: index.html | 내부 |
| `./site/guides/open-rag-trace-samples/index.html` | HTML | misc | lens:제품;type:소스 | 포함 | - | 2026-01-28T17:55:07 | read-full | last: </html> | HTML text file: index.html | 내부 |
| `./site/mapping/component-to-whitepaper.yaml` | YAML | misc | lens:제품;type:소스 | 포함 | - | 2026-01-28T17:55:07 | read-full | last:           subsection: 모델 프로필 | YAML text file: component-to-whitepaper.yaml | 내부 |
| `./site/new_whitepaper/00_frontmatter/index.html` | HTML | misc | lens:제품;type:소스 | 포함 | - | 2026-01-28T17:55:07 | read-full | last: </html> | HTML text file: index.html | 내부 |
| `./site/new_whitepaper/01_overview/index.html` | HTML | misc | lens:제품;type:소스 | 포함 | - | 2026-01-28T17:55:07 | read-full | last: </html> | HTML text file: index.html | 내부 |
| `./site/new_whitepaper/02_architecture/index.html` | HTML | misc | lens:제품;type:소스 | 포함 | - | 2026-01-28T17:55:07 | read-full | last: </html> | HTML text file: index.html | 내부 |
| `./site/new_whitepaper/03_data_flow/index.html` | HTML | misc | lens:제품;type:소스 | 포함 | - | 2026-01-28T17:55:07 | read-full | last: </html> | HTML text file: index.html | 내부 |
| `./site/new_whitepaper/04_components/index.html` | HTML | misc | lens:제품;type:소스 | 포함 | - | 2026-01-28T17:55:07 | read-full | last: </html> | HTML text file: index.html | 내부 |
| `./site/new_whitepaper/05_expert_lenses/index.html` | HTML | misc | lens:제품;type:소스 | 포함 | - | 2026-01-28T17:55:07 | read-full | last: </html> | HTML text file: index.html | 내부 |
| `./site/new_whitepaper/06_implementation/index.html` | HTML | misc | lens:제품;type:소스 | 포함 | - | 2026-01-28T17:55:07 | read-full | last: </html> | HTML text file: index.html | 내부 |
| `./site/new_whitepaper/07_advanced/index.html` | HTML | misc | lens:제품;type:소스 | 포함 | - | 2026-01-28T17:55:07 | read-full | last: </html> | HTML text file: index.html | 내부 |
| `./site/new_whitepaper/08_customization/index.html` | HTML | misc | lens:제품;type:소스 | 포함 | - | 2026-01-28T17:55:07 | read-full | last: </html> | HTML text file: index.html | 내부 |
| `./site/new_whitepaper/09_quality/index.html` | HTML | misc | lens:제품;type:소스 | 포함 | - | 2026-01-28T17:55:07 | read-full | last: </html> | HTML text file: index.html | 내부 |
| `./site/new_whitepaper/10_performance/index.html` | HTML | misc | lens:제품;type:소스 | 포함 | - | 2026-01-28T17:55:07 | read-full | last: </html> | HTML text file: index.html | 내부 |
| `./site/new_whitepaper/11_security/index.html` | HTML | misc | lens:제품;type:소스 | 포함 | - | 2026-01-28T17:55:07 | read-full | last: </html> | HTML text file: index.html | 내부 |
| `./site/new_whitepaper/12_operations/index.html` | HTML | misc | lens:제품;type:소스 | 포함 | - | 2026-01-28T17:55:07 | read-full | last: </html> | HTML text file: index.html | 내부 |
| `./site/new_whitepaper/13_standards/index.html` | HTML | misc | lens:제품;type:소스 | 포함 | - | 2026-01-28T17:55:07 | read-full | last: </html> | HTML text file: index.html | 내부 |
| `./site/new_whitepaper/14_roadmap/index.html` | HTML | misc | lens:제품;type:소스 | 포함 | - | 2026-01-28T17:55:07 | read-full | last: </html> | HTML text file: index.html | 내부 |
| `./site/new_whitepaper/INDEX/index.html` | HTML | misc | lens:제품;type:소스 | 포함 | - | 2026-01-28T17:55:07 | read-full | last: </html> | HTML text file: index.html | 내부 |
| `./site/new_whitepaper/STYLE_GUIDE/index.html` | HTML | misc | lens:제품;type:소스 | 포함 | - | 2026-01-28T17:55:07 | read-full | last: </html> | HTML text file: index.html | 내부 |
| `./site/objects.inv` | INV | misc | lens:제품;type:소스 | 포함 | - | 2026-01-28T17:55:07 | binary-scan | size: 6355 bytes | INV binary file (6355 bytes) | 내부 |
| `./site/search/search_index.json` | JSON | misc | lens:제품;type:소스 | 포함 | - | 2026-01-28T17:55:07 | read-full | keys: config,docs; last: {"config":{"lang":\["en","ko"\],"separator":"\[\\s\\-\]+","pipeline":\[" "\],"fields":{"title":{"boost":1000.0},"text":{"boost | JSON object with 2 keys | 내부 |
| `./site/sitemap.xml` | XML | misc | lens:제품;type:소스 | 포함 | - | 2026-01-28T17:55:07 | binary-scan | size: 5550 bytes | XML binary file (5550 bytes) | 내부 |
| `./site/sitemap.xml.gz` | GZ | misc | lens:제품;type:소스 | 포함 | - | 2026-01-28T17:55:07 | binary-scan | size: 620 bytes | GZ binary file (620 bytes) | 내부 |
| `./site/stylesheets/extra.css` | CSS | misc | lens:제품;type:소스 | 포함 | - | 2026-01-28T17:55:07 | read-full | last: } | CSS text file: extra.css | 내부 |
| `./site/tools/generate-whitepaper.py` | Python | misc | lens:제품;type:소스 | 포함 | - | 2026-01-28T17:55:07 | read-full | last:     main() | Python text file: generate-whitepaper.py | 내부 |
| `./src/evalvault/__init__.py` | Python | code-backend | lens:개발;type:소스 | 포함 | - | 2026-01-28T17:55:07 | read-full | last: _maybe_use_local_virtualenv() | Python text file: EvalVault package bootstrap. | 내부 |
| `./src/evalvault/adapters/__init__.py` | Python | code-backend | lens:개발;type:소스 | 포함 | - | 2026-01-28T17:55:07 | read-full | last: (empty) | Python text file: __init__.py | 내부 |
| `./src/evalvault/adapters/inbound/__init__.py` | Python | code-backend | lens:개발;type:소스 | 포함 | - | 2026-01-28T17:55:07 | read-full | last: __all__ = \["app", "mcp_tools"\] | Python text file: Inbound adapters. | 내부 |
| `./src/evalvault/adapters/inbound/api/__init__.py` | Python | code-backend | lens:개발;type:소스 | 포함 | - | 2026-01-28T17:55:07 | read-full | last: """EvalVault REST API Adapter.""" | Python text file: EvalVault REST API Adapter. | 내부 |
| `./src/evalvault/adapters/inbound/api/adapter.py` | Python | code-backend | lens:개발;type:소스 | 포함 | - | 2026-01-28T17:55:07 | read-full | last:     ) | Python text file: Web UI adapter implementing WebUIPort. | 내부 |
| `./src/evalvault/adapters/inbound/api/main.py` | Python | code-backend | lens:개발;type:소스 | 포함 | - | 2026-01-28T17:55:07 | read-full | last: AdapterDep = Annotated\[WebUIAdapter, Depends(get_web_adapter)\] | Python text file: FastAPI entry point for EvalVault API. | 내부 |
| `./src/evalvault/adapters/inbound/api/routers/__init__.py` | Python | code-backend | lens:개발;type:소스 | 포함 | - | 2026-01-28T17:55:07 | read-full | last: """API Routers.""" | Python text file: API Routers. | 내부 |
| `./src/evalvault/adapters/inbound/api/routers/benchmark.py` | Python | code-backend | lens:개발;type:소스 | 포함 | - | 2026-01-28T17:55:07 | read-full | last:         raise HTTPException(status_code=500, detail=str(e)) | Python text file: API Router for Benchmark Runs. | 내부 |
| `./src/evalvault/adapters/inbound/api/routers/calibration.py` | Python | code-backend | lens:개발;type:소스 | 포함 | - | 2026-01-28T17:55:07 | read-full | last:     return \[JudgeCalibrationHistoryItem.model_validate(entry) for entry in entries\] | Python text file: calibration.py | 내부 |
| `./src/evalvault/adapters/inbound/api/routers/chat.py` | Python | code-backend | lens:개발;type:소스 | 포함 | - | 2026-01-28T17:55:07 | read-full | last:     return StreamingResponse(event_generator(), media_type="application/x-ndjson") | Python text file: chat.py | 내부 |
| `./src/evalvault/adapters/inbound/api/routers/config.py` | Python | code-backend | lens:개발;type:소스 | 포함 | - | 2026-01-28T17:55:07 | read-full | last:     return profiles | Python text file: API Router for System Configuration. | 내부 |
| `./src/evalvault/adapters/inbound/api/routers/domain.py` | Python | code-backend | lens:개발;type:소스 | 포함 | - | 2026-01-28T17:55:07 | read-full | last:     \] | Python text file: API Router for Domain Memory. | 내부 |
| `./src/evalvault/adapters/inbound/api/routers/knowledge.py` | Python | code-backend | lens:개발;type:소스 | 포함 | - | 2026-01-28T17:55:07 | read-full | last:         return {"status": "error", "message": "Failed to load stats"} | Python text file: knowledge.py | 내부 |
| `./src/evalvault/adapters/inbound/api/routers/mcp.py` | Python | code-backend | lens:개발;type:소스 | 포함 | - | 2026-01-28T17:55:07 | read-full | last:     return _jsonrpc_error(request.id, -32601, "Method not found") | Python text file: mcp.py | 내부 |
| `./src/evalvault/adapters/inbound/api/routers/pipeline.py` | Python | code-backend | lens:개발;type:소스 | 포함 | - | 2026-01-28T17:55:07 | read-full | last:         raise HTTPException(status_code=500, detail=str(exc)) from exc | Python text file: pipeline.py | 내부 |
| `./src/evalvault/adapters/inbound/api/routers/runs.py` | Python | code-backend | lens:개발;type:소스 | 포함 | - | 2026-01-28T17:55:07 | read-full | last:         raise HTTPException(status_code=500, detail=str(e)) | Python text file: API Router for Evaluation Runs. | 내부 |
| `./src/evalvault/adapters/inbound/cli/__init__.py` | Python | code-backend | lens:개발;type:소스 | 포함 | - | 2026-01-28T17:55:07 | read-full | last: __all__ = \[name for name in globals() if not name.startswith("_") or name in HELPER_EXPORTS\] | Python text file: CLI application package exposing Typer app and legacy helpers. | 내부 |
| `./src/evalvault/adapters/inbound/cli/app.py` | Python | code-backend | lens:개발;type:소스 | 포함 | - | 2026-01-28T17:55:07 | read-full | last:     app() | Python text file: CLI interface for EvalVault using Typer. | 내부 |
| `./src/evalvault/adapters/inbound/cli/commands/__init__.py` | Python | code-backend | lens:개발;type:소스 | 포함 | - | 2026-01-28T17:55:07 | read-full | last: \] | Python text file: Command registration helpers for the EvalVault CLI package. | 내부 |
| `./src/evalvault/adapters/inbound/cli/commands/agent.py` | Python | code-backend | lens:개발;type:소스 | 포함 | - | 2026-01-28T17:55:07 | read-full | last:     app.add_typer(agent_app) | Python text file: `evalvault agent` command module. | 내부 |
| `./src/evalvault/adapters/inbound/cli/commands/analyze.py` | Python | code-backend | lens:개발;type:소스 | 포함 | - | 2026-01-28T17:55:07 | read-full | last: \] | Python text file: EvalVault CLI의 분석 관련 명령. | 내부 |
| `./src/evalvault/adapters/inbound/cli/commands/api.py` | Python | code-backend | lens:개발;type:소스 | 포함 | - | 2026-01-28T17:55:07 | read-full | last: __all__ = \["register_api_command"\] | Python text file: API server command for EvalVault CLI. | 내부 |
| `./src/evalvault/adapters/inbound/cli/commands/artifacts.py` | Python | code-backend | lens:개발;type:소스 | 포함 | - | 2026-01-28T17:55:07 | read-full | last:     } | Python text file: artifacts.py | 내부 |
| `./src/evalvault/adapters/inbound/cli/commands/benchmark.py` | Python | code-backend | lens:개발;type:소스 | 포함 | - | 2026-01-28T17:55:07 | read-full | last: __all__ = \["create_benchmark_app"\] | Python text file: Benchmark subcommands for EvalVault CLI. | 내부 |
| `./src/evalvault/adapters/inbound/cli/commands/calibrate.py` | Python | code-backend | lens:개발;type:소스 | 포함 | - | 2026-01-28T17:55:07 | read-full | last:     return f"{value:.3f}" | Python text file: calibrate.py | 내부 |
| `./src/evalvault/adapters/inbound/cli/commands/calibrate_judge.py` | Python | code-backend | lens:개발;type:소스 | 포함 | - | 2026-01-28T17:55:07 | read-full | last:     return f"{value:.3f}" | Python text file: calibrate_judge.py | 내부 |
| `./src/evalvault/adapters/inbound/cli/commands/compare.py` | Python | code-backend | lens:개발;type:소스 | 포함 | - | 2026-01-28T17:55:07 | read-full | last: __all__ = \["register_compare_commands"\] | Python text file: compare.py | 내부 |
| `./src/evalvault/adapters/inbound/cli/commands/config.py` | Python | code-backend | lens:개발;type:소스 | 포함 | - | 2026-01-28T17:55:07 | read-full | last: __all__ = \["register_config_commands"\] | Python text file: Configuration/diagnostics commands for EvalVault CLI. | 내부 |
| `./src/evalvault/adapters/inbound/cli/commands/debug.py` | Python | code-backend | lens:개발;type:소스 | 포함 | - | 2026-01-28T17:55:07 | read-full | last:     return debug_app | Python text file: Debug report commands for the EvalVault CLI. | 내부 |
| `./src/evalvault/adapters/inbound/cli/commands/domain.py` | Python | code-backend | lens:개발;type:소스 | 포함 | - | 2026-01-28T17:55:07 | read-full | last: __all__ = \["create_domain_app"\] | Python text file: Domain memory management commands for EvalVault CLI. | 내부 |
| `./src/evalvault/adapters/inbound/cli/commands/experiment.py` | Python | code-backend | lens:개발;type:소스 | 포함 | - | 2026-01-28T17:55:07 | read-full | last: __all__ = \["register_experiment_commands"\] | Python text file: Experiment management commands for the EvalVault CLI. | 내부 |
| `./src/evalvault/adapters/inbound/cli/commands/gate.py` | Python | code-backend | lens:개발;type:소스 | 포함 | - | 2026-01-28T17:55:07 | read-full | last: __all__ = \["register_gate_commands"\] | Python text file: Quality gate command registration for EvalVault CLI. | 내부 |
| `./src/evalvault/adapters/inbound/cli/commands/generate.py` | Python | code-backend | lens:개발;type:소스 | 포함 | - | 2026-01-28T17:55:07 | read-full | last: __all__ = \["register_generate_commands"\] | Python text file: `evalvault generate` 명령을 등록하는 모듈. | 내부 |
| `./src/evalvault/adapters/inbound/cli/commands/graph_rag.py` | Python | code-backend | lens:개발;type:소스 | 포함 | - | 2026-01-28T17:55:07 | read-full | last: __all__ = \["create_graph_rag_app"\] | Python text file: GraphRAG experiment commands for the EvalVault CLI. | 내부 |
| `./src/evalvault/adapters/inbound/cli/commands/history.py` | Python | code-backend | lens:개발;type:소스 | 포함 | - | 2026-01-28T17:55:07 | read-full | last: __all__ = \["register_history_commands"\] | Python text file: History/compare/export commands for the EvalVault CLI. | 내부 |
| `./src/evalvault/adapters/inbound/cli/commands/init.py` | Python | code-backend | lens:개발;type:소스 | 포함 | - | 2026-01-28T17:55:07 | read-full | last: __all__ = \["register_init_command"\] | Python text file: Init command for new user onboarding. | 내부 |
| `./src/evalvault/adapters/inbound/cli/commands/kg.py` | Python | code-backend | lens:개발;type:소스 | 포함 | - | 2026-01-28T17:55:07 | read-full | last: \] | Python text file: Knowledge graph utilities for the EvalVault CLI. | 내부 |
| `./src/evalvault/adapters/inbound/cli/commands/langfuse.py` | Python | code-backend | lens:개발;type:소스 | 포함 | - | 2026-01-28T17:55:07 | read-full | last: __all__ = \["register_langfuse_commands", "_fetch_langfuse_traces"\] | Python text file: Langfuse dashboard command for EvalVault CLI. | 내부 |
| `./src/evalvault/adapters/inbound/cli/commands/method.py` | Python | code-backend | lens:개발;type:소스 | 포함 | - | 2026-01-28T17:55:07 | read-full | last: __all__ = \["create_method_app"\] | Python text file: CLI commands for method plugins. | 내부 |
| `./src/evalvault/adapters/inbound/cli/commands/ops.py` | Python | code-backend | lens:개발;type:소스 | 포함 | - | 2026-01-28T17:55:07 | read-full | last: __all__ = \["create_ops_app"\] | Python text file: ops.py | 내부 |
| `./src/evalvault/adapters/inbound/cli/commands/phoenix.py` | Python | code-backend | lens:개발;type:소스 | 포함 | - | 2026-01-28T17:55:07 | read-full | last: __all__ = \["create_phoenix_app"\] | Python text file: Phoenix helper commands (dataset exports, observability tooling). | 내부 |
| `./src/evalvault/adapters/inbound/cli/commands/pipeline.py` | Python | code-backend | lens:개발;type:소스 | 포함 | - | 2026-01-28T17:55:07 | read-full | last: __all__ = \["register_pipeline_commands"\] | Python text file: Pipeline command group for EvalVault CLI. | 내부 |
| `./src/evalvault/adapters/inbound/cli/commands/profile_difficulty.py` | Python | code-backend | lens:개발;type:소스 | 포함 | - | 2026-01-28T17:55:07 | read-full | last: __all__ = \["register_profile_difficulty_commands"\] | Python text file: profile_difficulty.py | 내부 |
| `./src/evalvault/adapters/inbound/cli/commands/prompts.py` | Python | code-backend | lens:개발;type:소스 | 포함 | - | 2026-01-28T17:55:07 | read-full | last: __all__ = \["create_prompts_app"\] | Python text file: Prompt snapshot commands for the EvalVault CLI. | 내부 |
| `./src/evalvault/adapters/inbound/cli/commands/regress.py` | Python | code-backend | lens:개발;type:소스 | 포함 | - | 2026-01-28T17:55:07 | read-full | last: __all__ = \["register_regress_commands"\] | Python text file: regress.py | 내부 |
| `./src/evalvault/adapters/inbound/cli/commands/run.py` | Python | code-backend | lens:개발;type:소스 | 포함 | - | 2026-01-28T17:55:07 | read-full | last: \] | Python text file: `evalvault run` 명령 전용 Typer 등록 모듈. | 내부 |
| `./src/evalvault/adapters/inbound/cli/commands/run_helpers.py` | Python | code-backend | lens:개발;type:소스 | 포함 | - | 2026-01-28T17:55:07 | read-full | last:     console.print(Panel(body, title=f"Run Mode: {preset.label}", border_style=border_style)) | Python text file: `evalvault run` 명령을 보조하는 헬퍼 모음. | 내부 |
| `./src/evalvault/adapters/inbound/cli/commands/stage.py` | Python | code-backend | lens:개발;type:소스 | 포함 | - | 2026-01-28T17:55:07 | read-full | last:     console.print(table) | Python text file: Stage event commands for the EvalVault CLI. | 내부 |
| `./src/evalvault/adapters/inbound/cli/utils/__init__.py` | Python | code-backend | lens:개발;type:소스 | 포함 | - | 2026-01-28T17:55:07 | read-full | last: \] | Python text file: Common helpers for CLI commands (formatters, validators, etc.). | 내부 |
| `./src/evalvault/adapters/inbound/cli/utils/analysis_io.py` | Python | code-backend | lens:개발;type:소스 | 포함 | - | 2026-01-28T17:55:07 | read-full | last:         return str(target) | Python text file: Helpers for analysis pipeline IO. | 내부 |
| `./src/evalvault/adapters/inbound/cli/utils/console.py` | Python | code-backend | lens:개발;type:소스 | 포함 | - | 2026-01-28T17:55:07 | read-full | last:         yield update | Python text file: Common console helpers for CLI UX (errors, warnings, progress bars). | 내부 |
| `./src/evalvault/adapters/inbound/cli/utils/errors.py` | Python | code-backend | lens:개발;type:소스 | 포함 | - | 2026-01-28T17:55:07 | read-full | last: \] | Python text file: Enhanced error handling utilities for CLI with actionable guidance. | 내부 |
| `./src/evalvault/adapters/inbound/cli/utils/formatters.py` | Python | code-backend | lens:개발;type:소스 | 포함 | - | 2026-01-28T17:55:07 | read-full | last:     return f"\[{color}\]{value:+.{precision}f}\[/{color}\]" | Python text file: Shared formatting helpers for CLI output. | 내부 |
| `./src/evalvault/adapters/inbound/cli/utils/options.py` | Python | code-backend | lens:개발;type:소스 | 포함 | - | 2026-01-28T17:55:07 | read-full | last:     return Path(value) | Python text file: Common Typer option factories for CLI commands. | 내부 |
| `./src/evalvault/adapters/inbound/cli/utils/presets.py` | Python | code-backend | lens:개발;type:소스 | 포함 | - | 2026-01-28T17:55:07 | read-full | last: \] | Python text file: Preset system for common evaluation configurations. | 내부 |
| `./src/evalvault/adapters/inbound/cli/utils/progress.py` | Python | code-backend | lens:개발;type:소스 | 포함 | - | 2026-01-28T17:55:07 | read-full | last: \] | Python text file: Progress bar utilities with ETA calculation for CLI. | 내부 |
| `./src/evalvault/adapters/inbound/cli/utils/validators.py` | Python | code-backend | lens:개발;type:소스 | 포함 | - | 2026-01-28T17:55:07 | read-full | last:     raise typer.Exit(1) | Python text file: Shared validation helpers for CLI commands. | 내부 |
| `./src/evalvault/adapters/inbound/mcp/__init__.py` | Python | code-backend | lens:개발;type:소스 | 포함 | - | 2026-01-28T17:55:07 | read-full | last: \] | Python text file: MCP inbound adapter package. | 내부 |
| `./src/evalvault/adapters/inbound/mcp/schemas.py` | Python | code-backend | lens:개발;type:소스 | 포함 | - | 2026-01-28T17:55:07 | read-full | last:     errors: list\[McpError\] = Field(default_factory=list) | Python text file: schemas.py | 내부 |
| `./src/evalvault/adapters/inbound/mcp/tools.py` | Python | code-backend | lens:개발;type:소스 | 포함 | - | 2026-01-28T17:55:07 | read-full | last: ) | Python text file: tools.py | 내부 |
| `./src/evalvault/adapters/outbound/__init__.py` | Python | code-backend | lens:개발;type:소스 | 포함 | - | 2026-01-28T17:55:07 | read-full | last: (empty) | Python text file: __init__.py | 내부 |
| `./src/evalvault/adapters/outbound/analysis/__init__.py` | Python | code-backend | lens:개발;type:소스 | 포함 | - | 2026-01-28T17:55:07 | read-full | last: \] | Python text file: Analysis adapters. | 내부 |
| `./src/evalvault/adapters/outbound/analysis/analysis_report_module.py` | Python | code-backend | lens:개발;type:소스 | 포함 | - | 2026-01-28T17:55:07 | read-full | last:         } | Python text file: Phase 14.4: Analysis Report Module. | 내부 |
| `./src/evalvault/adapters/outbound/analysis/base_module.py` | Python | code-backend | lens:개발;type:소스 | 포함 | - | 2026-01-28T17:55:07 | read-full | last:         return self.execute(inputs, params) | Python text file: Phase 14.4: Base Analysis Module. | 내부 |
| `./src/evalvault/adapters/outbound/analysis/bm25_searcher_module.py` | Python | code-backend | lens:개발;type:소스 | 포함 | - | 2026-01-28T17:55:07 | read-full | last:         } | Python text file: BM25 searcher module. | 내부 |
| `./src/evalvault/adapters/outbound/analysis/causal_adapter.py` | Python | code-backend | lens:개발;type:소스 | 포함 | - | 2026-01-28T17:55:07 | read-full | last:         return insights | Python text file: Causal analysis adapter implementation. | 내부 |
| `./src/evalvault/adapters/outbound/analysis/causal_analyzer_module.py` | Python | code-backend | lens:개발;type:소스 | 포함 | - | 2026-01-28T17:55:07 | read-full | last:         ) | Python text file: Phase 14.4: Causal Analyzer Module. | 내부 |
| `./src/evalvault/adapters/outbound/analysis/common.py` | Python | code-backend | lens:개발;type:소스 | 포함 | - | 2026-01-28T17:55:07 | read-full | last:         ) | Python text file: 공통 분석 어댑터 유틸리티. | 내부 |
| `./src/evalvault/adapters/outbound/analysis/comparison_pipeline_adapter.py` | Python | code-backend | lens:개발;type:소스 | 포함 | - | 2026-01-28T17:55:07 | read-full | last: __all__ = \["ComparisonPipelineAdapter"\] | Python text file: comparison_pipeline_adapter.py | 내부 |
| `./src/evalvault/adapters/outbound/analysis/comparison_report_module.py` | Python | code-backend | lens:개발;type:소스 | 포함 | - | 2026-01-28T17:55:07 | read-full | last:         } | Python text file: Phase 14.4: Comparison Report Module. | 내부 |
| `./src/evalvault/adapters/outbound/analysis/data_loader_module.py` | Python | code-backend | lens:개발;type:소스 | 포함 | - | 2026-01-28T17:55:07 | read-full | last:         } | Python text file: Phase 14.4: Data Loader Module. | 내부 |
| `./src/evalvault/adapters/outbound/analysis/detailed_report_module.py` | Python | code-backend | lens:개발;type:소스 | 포함 | - | 2026-01-28T17:55:07 | read-full | last:         } | Python text file: Detailed report module. | 내부 |
| `./src/evalvault/adapters/outbound/analysis/diagnostic_playbook_module.py` | Python | code-backend | lens:개발;type:소스 | 포함 | - | 2026-01-28T17:55:07 | read-full | last:         return default_threshold | Python text file: Diagnostic playbook module. | 내부 |
| `./src/evalvault/adapters/outbound/analysis/embedding_analyzer_module.py` | Python | code-backend | lens:개발;type:소스 | 포함 | - | 2026-01-28T17:55:07 | read-full | last:         return embeddings, meta, errors | Python text file: Embedding analyzer module. | 내부 |
| `./src/evalvault/adapters/outbound/analysis/embedding_distribution_module.py` | Python | code-backend | lens:개발;type:소스 | 포함 | - | 2026-01-28T17:55:07 | read-full | last:         } | Python text file: Embedding distribution checker module. | 내부 |
| `./src/evalvault/adapters/outbound/analysis/embedding_searcher_module.py` | Python | code-backend | lens:개발;type:소스 | 포함 | - | 2026-01-28T17:55:07 | read-full | last:         } | Python text file: Embedding searcher module. | 내부 |
| `./src/evalvault/adapters/outbound/analysis/hybrid_rrf_module.py` | Python | code-backend | lens:개발;type:소스 | 포함 | - | 2026-01-28T17:55:07 | read-full | last:         } | Python text file: Hybrid RRF search module. | 내부 |
| `./src/evalvault/adapters/outbound/analysis/hybrid_weighted_module.py` | Python | code-backend | lens:개발;type:소스 | 포함 | - | 2026-01-28T17:55:07 | read-full | last:         } | Python text file: Weighted hybrid search module. | 내부 |
| `./src/evalvault/adapters/outbound/analysis/hypothesis_generator_module.py` | Python | code-backend | lens:개발;type:소스 | 포함 | - | 2026-01-28T17:55:07 | read-full | last:         return patterns | Python text file: hypothesis_generator_module.py | 내부 |
| `./src/evalvault/adapters/outbound/analysis/llm_report_module.py` | Python | code-backend | lens:개발;type:소스 | 포함 | - | 2026-01-28T17:55:07 | read-full | last:         ) | Python text file: LLM-powered analysis report module with evidence support. | 내부 |
| `./src/evalvault/adapters/outbound/analysis/low_performer_extractor_module.py` | Python | code-backend | lens:개발;type:소스 | 포함 | - | 2026-01-28T17:55:07 | read-full | last:         } | Python text file: Low performer extractor module. | 내부 |
| `./src/evalvault/adapters/outbound/analysis/model_analyzer_module.py` | Python | code-backend | lens:개발;type:소스 | 포함 | - | 2026-01-28T17:55:07 | read-full | last:         } | Python text file: Model analyzer module. | 내부 |
| `./src/evalvault/adapters/outbound/analysis/morpheme_analyzer_module.py` | Python | code-backend | lens:개발;type:소스 | 포함 | - | 2026-01-28T17:55:07 | read-full | last:         } | Python text file: Morpheme analyzer module. | 내부 |
| `./src/evalvault/adapters/outbound/analysis/morpheme_quality_checker_module.py` | Python | code-backend | lens:개발;type:소스 | 포함 | - | 2026-01-28T17:55:07 | read-full | last:         } | Python text file: Morpheme quality checker module. | 내부 |
| `./src/evalvault/adapters/outbound/analysis/multiturn_analyzer_module.py` | Python | code-backend | lens:개발;type:소스 | 포함 | - | 2026-01-28T17:55:07 | read-full | last:     } | Python text file: 멀티턴 평가 요약 모듈입니다. | 내부 |
| `./src/evalvault/adapters/outbound/analysis/network_analyzer_module.py` | Python | code-backend | lens:개발;type:소스 | 포함 | - | 2026-01-28T17:55:07 | read-full | last:         return insights | Python text file: network_analyzer_module.py | 내부 |
| `./src/evalvault/adapters/outbound/analysis/nlp_adapter.py` | Python | code-backend | lens:개발;type:소스 | 포함 | - | 2026-01-28T17:55:07 | read-full | last:             return \[\] | Python text file: NLP 분석 어댑터. | 내부 |
| `./src/evalvault/adapters/outbound/analysis/nlp_analyzer_module.py` | Python | code-backend | lens:개발;type:소스 | 포함 | - | 2026-01-28T17:55:07 | read-full | last:         return serialized | Python text file: Phase 14.4: NLP Analyzer Module. | 내부 |
| `./src/evalvault/adapters/outbound/analysis/pattern_detector_module.py` | Python | code-backend | lens:개발;type:소스 | 포함 | - | 2026-01-28T17:55:07 | read-full | last:         } | Python text file: Pattern detector module. | 내부 |
| `./src/evalvault/adapters/outbound/analysis/pipeline_factory.py` | Python | code-backend | lens:개발;type:소스 | 포함 | - | 2026-01-28T17:55:07 | read-full | last:     return service | Python text file: Analysis pipeline factory for CLI/API usage. | 내부 |
| `./src/evalvault/adapters/outbound/analysis/pipeline_helpers.py` | Python | code-backend | lens:개발;type:소스 | 포함 | - | 2026-01-28T17:55:07 | read-full | last:     return hits / len(relevant_set) | Python text file: Helpers for pipeline analysis modules. | 내부 |
| `./src/evalvault/adapters/outbound/analysis/priority_summary_module.py` | Python | code-backend | lens:개발;type:소스 | 포함 | - | 2026-01-28T17:55:07 | read-full | last:             return None | Python text file: Priority summary module for identifying high-impact cases. | 내부 |
| `./src/evalvault/adapters/outbound/analysis/ragas_evaluator_module.py` | Python | code-backend | lens:개발;type:소스 | 포함 | - | 2026-01-28T17:55:07 | read-full | last:         ) | Python text file: RAGAS evaluator module for pipeline. | 내부 |
| `./src/evalvault/adapters/outbound/analysis/retrieval_analyzer_module.py` | Python | code-backend | lens:개발;type:소스 | 포함 | - | 2026-01-28T17:55:07 | read-full | last:     return output | Python text file: Retrieval analyzer module. | 내부 |
| `./src/evalvault/adapters/outbound/analysis/retrieval_benchmark_module.py` | Python | code-backend | lens:개발;type:소스 | 포함 | - | 2026-01-28T17:55:07 | read-full | last:         return insights | Python text file: Retrieval benchmark module. | 내부 |
| `./src/evalvault/adapters/outbound/analysis/retrieval_quality_checker_module.py` | Python | code-backend | lens:개발;type:소스 | 포함 | - | 2026-01-28T17:55:07 | read-full | last:         } | Python text file: Retrieval quality checker module. | 내부 |
| `./src/evalvault/adapters/outbound/analysis/root_cause_analyzer_module.py` | Python | code-backend | lens:개발;type:소스 | 포함 | - | 2026-01-28T17:55:07 | read-full | last:         } | Python text file: Root cause analyzer module. | 내부 |
| `./src/evalvault/adapters/outbound/analysis/run_analyzer_module.py` | Python | code-backend | lens:개발;type:소스 | 포함 | - | 2026-01-28T17:55:07 | read-full | last:         } | Python text file: Run analyzer module. | 내부 |
| `./src/evalvault/adapters/outbound/analysis/run_change_detector_module.py` | Python | code-backend | lens:개발;type:소스 | 포함 | - | 2026-01-28T17:55:07 | read-full | last:         return \[{"field": field, "before": before, "after": after}\] | Python text file: Run change detector module. | 내부 |
| `./src/evalvault/adapters/outbound/analysis/run_comparator_module.py` | Python | code-backend | lens:개발;type:소스 | 포함 | - | 2026-01-28T17:55:07 | read-full | last:         return comparison | Python text file: Run comparator module. | 내부 |
| `./src/evalvault/adapters/outbound/analysis/run_loader_module.py` | Python | code-backend | lens:개발;type:소스 | 포함 | - | 2026-01-28T17:55:07 | read-full | last:         return \[run_a, run_b\] | Python text file: Run loader module. | 내부 |
| `./src/evalvault/adapters/outbound/analysis/run_metric_comparator_module.py` | Python | code-backend | lens:개발;type:소스 | 포함 | - | 2026-01-28T17:55:07 | read-full | last:         return notable | Python text file: Run metric comparator module. | 내부 |
| `./src/evalvault/adapters/outbound/analysis/search_comparator_module.py` | Python | code-backend | lens:개발;type:소스 | 포함 | - | 2026-01-28T17:55:07 | read-full | last:         } | Python text file: Search comparator module. | 내부 |
| `./src/evalvault/adapters/outbound/analysis/statistical_adapter.py` | Python | code-backend | lens:개발;type:소스 | 포함 | - | 2026-01-28T17:55:07 | read-full | last:         return insights | Python text file: 통계 분석 어댑터. | 내부 |
| `./src/evalvault/adapters/outbound/analysis/statistical_analyzer_module.py` | Python | code-backend | lens:개발;type:소스 | 포함 | - | 2026-01-28T17:55:07 | read-full | last:         ) | Python text file: Phase 14.4: Statistical Analyzer Module. | 내부 |
| `./src/evalvault/adapters/outbound/analysis/statistical_comparator_module.py` | Python | code-backend | lens:개발;type:소스 | 포함 | - | 2026-01-28T17:55:07 | read-full | last:         return comparison | Python text file: Statistical comparator module. | 내부 |
| `./src/evalvault/adapters/outbound/analysis/summary_report_module.py` | Python | code-backend | lens:개발;type:소스 | 포함 | - | 2026-01-28T17:55:07 | read-full | last:         } | Python text file: Phase 14.4: Summary Report Module. | 내부 |
| `./src/evalvault/adapters/outbound/analysis/time_series_analyzer_module.py` | Python | code-backend | lens:개발;type:소스 | 포함 | - | 2026-01-28T17:55:07 | read-full | last:         } | Python text file: Time series analyzer module. | 내부 |
| `./src/evalvault/adapters/outbound/analysis/timeseries_advanced_module.py` | Python | code-backend | lens:개발;type:소스 | 포함 | - | 2026-01-28T17:55:07 | read-full | last:         return insights | Python text file: timeseries_advanced_module.py | 내부 |
| `./src/evalvault/adapters/outbound/analysis/trend_detector_module.py` | Python | code-backend | lens:개발;type:소스 | 포함 | - | 2026-01-28T17:55:07 | read-full | last:         } | Python text file: Trend detector module. | 내부 |
| `./src/evalvault/adapters/outbound/analysis/verification_report_module.py` | Python | code-backend | lens:개발;type:소스 | 포함 | - | 2026-01-28T17:55:07 | read-full | last:         } | Python text file: Phase 14.4: Verification Report Module. | 내부 |
| `./src/evalvault/adapters/outbound/artifact_fs.py` | Python | code-backend | lens:개발;type:소스 | 포함 | - | 2026-01-28T17:55:07 | read-full | last:         return path.read_text(encoding="utf-8") | Python text file: artifact_fs.py | 내부 |
| `./src/evalvault/adapters/outbound/benchmark/__init__.py` | Python | code-backend | lens:개발;type:소스 | 포함 | - | 2026-01-28T17:55:07 | read-full | last: __all__ = \["LMEvalAdapter"\] | Python text file: Benchmark adapters for external evaluation frameworks. | 내부 |
| `./src/evalvault/adapters/outbound/benchmark/lm_eval_adapter.py` | Python | code-backend | lens:개발;type:소스 | 포함 | - | 2026-01-28T17:55:07 | read-full | last:     return LMEvalAdapter(settings=settings) | Python text file: lm-evaluation-harness adapter for EvalVault benchmark integration. | 내부 |
| `./src/evalvault/adapters/outbound/cache/__init__.py` | Python | code-backend | lens:개발;type:소스 | 포함 | - | 2026-01-28T17:55:07 | read-full | last: \] | Python text file: Cache adapters. | 내부 |
| `./src/evalvault/adapters/outbound/cache/hybrid_cache.py` | Python | code-backend | lens:개발;type:소스 | 포함 | - | 2026-01-28T17:55:07 | read-full | last: __all__ = \["HybridCache", "CacheEntry", "make_cache_key"\] | Python text file: LRU + TTL 하이브리드 캐시 어댑터. | 내부 |
| `./src/evalvault/adapters/outbound/cache/memory_cache.py` | Python | code-backend | lens:개발;type:소스 | 포함 | - | 2026-01-28T17:55:07 | read-full | last:             return len(expired_keys) | Python text file: 인메모리 캐시 어댑터. | 내부 |
| `./src/evalvault/adapters/outbound/dataset/__init__.py` | Python | code-backend | lens:개발;type:소스 | 포함 | - | 2026-01-28T17:55:07 | read-full | last: \] | Python text file: Dataset loaders for various file formats. | 내부 |
| `./src/evalvault/adapters/outbound/dataset/base.py` | Python | code-backend | lens:개발;type:소스 | 포함 | - | 2026-01-28T17:55:07 | read-full | last:         return "1.0.0" | Python text file: Base dataset loader implementation. | 내부 |
| `./src/evalvault/adapters/outbound/dataset/csv_loader.py` | Python | code-backend | lens:개발;type:소스 | 포함 | - | 2026-01-28T17:55:07 | read-full | last:         return dataset | Python text file: CSV dataset loader implementation. | 내부 |
| `./src/evalvault/adapters/outbound/dataset/excel_loader.py` | Python | code-backend | lens:개발;type:소스 | 포함 | - | 2026-01-28T17:55:07 | read-full | last:         return dataset | Python text file: Excel dataset loader implementation. | 내부 |
| `./src/evalvault/adapters/outbound/dataset/json_loader.py` | Python | code-backend | lens:개발;type:소스 | 포함 | - | 2026-01-28T17:55:07 | read-full | last:         return dataset | Python text file: JSON dataset loader implementation. | 내부 |
| `./src/evalvault/adapters/outbound/dataset/loader_factory.py` | Python | code-backend | lens:개발;type:소스 | 포함 | - | 2026-01-28T17:55:07 | read-full | last:         _LOADERS.append(loader_class) | Python text file: Factory for creating appropriate dataset loaders. | 내부 |
| `./src/evalvault/adapters/outbound/dataset/method_input_loader.py` | Python | code-backend | lens:개발;type:소스 | 포함 | - | 2026-01-28T17:55:07 | read-full | last:         return path | Python text file: Loader for base question datasets used by method plugins. | 내부 |
| `./src/evalvault/adapters/outbound/dataset/multiturn_json_loader.py` | Python | code-backend | lens:개발;type:소스 | 포함 | - | 2026-01-28T17:55:07 | read-full | last:     ) | Python text file: multiturn_json_loader.py | 내부 |
| `./src/evalvault/adapters/outbound/dataset/streaming_loader.py` | Python | code-backend | lens:개발;type:소스 | 포함 | - | 2026-01-28T17:55:07 | read-full | last: \] | Python text file: 스트리밍 데이터셋 로더. | 내부 |
| `./src/evalvault/adapters/outbound/dataset/templates.py` | Python | code-backend | lens:개발;type:소스 | 포함 | - | 2026-01-28T17:55:07 | read-full | last: \] | Python text file: Dataset template generators for JSON/CSV/XLSX. | 내부 |
| `./src/evalvault/adapters/outbound/dataset/thresholds.py` | Python | code-backend | lens:개발;type:소스 | 포함 | - | 2026-01-28T17:55:07 | read-full | last:     return thresholds | Python text file: Helpers for dataset-level threshold columns. | 내부 |
| `./src/evalvault/adapters/outbound/debug/__init__.py` | Python | code-backend | lens:개발;type:소스 | 포함 | - | 2026-01-28T17:55:07 | read-full | last: __all__ = \["render_json", "render_markdown"\] | Python text file: Debug report renderers. | 내부 |
| `./src/evalvault/adapters/outbound/debug/report_renderer.py` | Python | code-backend | lens:개발;type:소스 | 포함 | - | 2026-01-28T17:55:07 | read-full | last:     return max(metric.threshold - metric.score, 0.0) | Python text file: Render debug reports to Markdown or JSON. | 내부 |
| `./src/evalvault/adapters/outbound/documents/__init__.py` | Python | code-backend | lens:개발;type:소스 | 포함 | - | 2026-01-28T17:55:07 | read-full | last: \] | Python text file: __init__.py | 내부 |
| `./src/evalvault/adapters/outbound/documents/ocr/__init__.py` | Python | code-backend | lens:개발;type:소스 | 포함 | - | 2026-01-28T17:55:07 | read-full | last: \] | Python text file: __init__.py | 내부 |
| `./src/evalvault/adapters/outbound/documents/ocr/paddleocr_backend.py` | Python | code-backend | lens:개발;type:소스 | 포함 | - | 2026-01-28T17:55:07 | read-full | last:     return "\n".join(parts).strip() | Python text file: paddleocr_backend.py | 내부 |
| `./src/evalvault/adapters/outbound/documents/pdf_extractor.py` | Python | code-backend | lens:개발;type:소스 | 포함 | - | 2026-01-28T17:55:07 | read-full | last:     raise ValueError(f"Unsupported OCR backend: {ocr_backend}") | Python text file: pdf_extractor.py | 내부 |
| `./src/evalvault/adapters/outbound/documents/versioned_loader.py` | Python | code-backend | lens:개발;type:소스 | 포함 | - | 2026-01-28T17:55:07 | read-full | last:     return " ".join(text.split()) | Python text file: versioned_loader.py | 내부 |
| `./src/evalvault/adapters/outbound/domain_memory/__init__.py` | Python | code-backend | lens:개발;type:소스 | 포함 | - | 2026-01-28T17:55:07 | read-full | last: __all__ = \["SQLiteDomainMemoryAdapter"\] | Python text file: Domain Memory adapters for factual, experiential, and working memory layers. | 내부 |
| `./src/evalvault/adapters/outbound/domain_memory/domain_memory_schema.sql` | SQL | code-backend | lens:개발;type:소스 | 포함 | - | 2026-01-28T17:55:07 | binary-scan | size: 11268 bytes | SQL binary file (11268 bytes) | 내부 |
| `./src/evalvault/adapters/outbound/domain_memory/sqlite_adapter.py` | Python | code-backend | lens:개발;type:소스 | 포함 | - | 2026-01-28T17:55:07 | read-full | last:             conn.close() | Python text file: SQLite adapter for Domain Memory storage. | 내부 |
| `./src/evalvault/adapters/outbound/filesystem/__init__.py` | Python | code-backend | lens:개발;type:소스 | 포함 | - | 2026-01-28T17:55:07 | read-full | last: __all__ = \["OpsSnapshotWriter"\] | Python text file: __init__.py | 내부 |
| `./src/evalvault/adapters/outbound/filesystem/difficulty_profile_writer.py` | Python | code-backend | lens:개발;type:소스 | 포함 | - | 2026-01-28T17:55:07 | read-full | last:         return artifacts_index | Python text file: difficulty_profile_writer.py | 내부 |
| `./src/evalvault/adapters/outbound/filesystem/ops_snapshot_writer.py` | Python | code-backend | lens:개발;type:소스 | 포함 | - | 2026-01-28T17:55:07 | read-full | last:         write_json(path, payload) | Python text file: ops_snapshot_writer.py | 내부 |
| `./src/evalvault/adapters/outbound/improvement/__init__.py` | Python | code-backend | lens:개발;type:소스 | 포함 | - | 2026-01-28T17:55:07 | read-full | last: \] | Python text file: Improvement adapters for RAG system optimization. | 내부 |
| `./src/evalvault/adapters/outbound/improvement/insight_generator.py` | Python | code-backend | lens:개발;type:소스 | 포함 | - | 2026-01-28T17:55:07 | read-full | last:         return insight | Python text file: LLM-based insight generator for RAG improvement. | 내부 |
| `./src/evalvault/adapters/outbound/improvement/pattern_detector.py` | Python | code-backend | lens:개발;type:소스 | 포함 | - | 2026-01-28T17:55:07 | read-full | last:         return overlap < 0.5 | Python text file: Rule-based pattern detector for RAG improvement. | 내부 |
| `./src/evalvault/adapters/outbound/improvement/playbook_loader.py` | Python | code-backend | lens:개발;type:소스 | 포함 | - | 2026-01-28T17:55:07 | read-full | last:     return _default_loader.load() | Python text file: Playbook loader for improvement rules. | 내부 |
| `./src/evalvault/adapters/outbound/improvement/stage_metric_playbook_loader.py` | Python | code-backend | lens:개발;type:소스 | 포함 | - | 2026-01-28T17:55:07 | read-full | last:         return self._playbook | Python text file: Stage metric playbook loader. | 내부 |
| `./src/evalvault/adapters/outbound/judge_calibration_adapter.py` | Python | code-backend | lens:개발;type:소스 | 포함 | - | 2026-01-28T17:55:07 | read-full | last:         ) | Python text file: judge_calibration_adapter.py | 내부 |
| `./src/evalvault/adapters/outbound/judge_calibration_reporter.py` | Python | code-backend | lens:개발;type:소스 | 포함 | - | 2026-01-28T17:55:07 | read-full | last:         return {"dir": str(artifacts_dir), "index": str(index_path)} | Python text file: judge_calibration_reporter.py | 내부 |
| `./src/evalvault/adapters/outbound/kg/__init__.py` | Python | code-backend | lens:개발;type:소스 | 포함 | - | 2026-01-28T17:55:07 | read-full | last: \] | Python text file: Knowledge Graph adapters for EvalVault. | 내부 |
| `./src/evalvault/adapters/outbound/kg/graph_rag_retriever.py` | Python | code-backend | lens:개발;type:소스 | 포함 | - | 2026-01-28T17:55:07 | read-full | last:             self._query_cache.popitem(last=False) | Python text file: GraphRAG-style retriever combining KG signals with BM25/Dense results. | 내부 |
| `./src/evalvault/adapters/outbound/kg/networkx_adapter.py` | Python | code-backend | lens:개발;type:소스 | 포함 | - | 2026-01-28T17:55:07 | read-full | last:         ) | Python text file: NetworkX-based Knowledge Graph adapter. | 내부 |
| `./src/evalvault/adapters/outbound/kg/parallel_kg_builder.py` | Python | code-backend | lens:개발;type:소스 | 포함 | - | 2026-01-28T17:55:07 | read-full | last: __all__ = \["KGBuildResult", "KGBuilderStats", "ParallelKGBuilder"\] | Python text file: Parallel KG builder for large document collections. | 내부 |
| `./src/evalvault/adapters/outbound/kg/query_strategies.py` | Python | code-backend | lens:개발;type:소스 | 포함 | - | 2026-01-28T17:55:07 | read-full | last:         return \[s.get_strategy_name() for s in self._strategies\] | Python text file: Query generation strategies for Knowledge Graph-based testset generation. | 내부 |
| `./src/evalvault/adapters/outbound/llm/__init__.py` | Python | code-backend | lens:개발;type:소스 | 포함 | - | 2026-01-28T17:55:07 | read-full | last: \] | Python text file: __init__.py | 내부 |
| `./src/evalvault/adapters/outbound/llm/anthropic_adapter.py` | Python | code-backend | lens:개발;type:소스 | 포함 | - | 2026-01-28T17:55:07 | read-full | last:             return asyncio.run(self.agenerate_text(prompt, options=options)) | Python text file: Anthropic Claude LLM adapter for Ragas evaluation. | 내부 |
| `./src/evalvault/adapters/outbound/llm/azure_adapter.py` | Python | code-backend | lens:개발;type:소스 | 포함 | - | 2026-01-28T17:55:07 | read-full | last:         return super().as_ragas_embeddings() | Python text file: Azure OpenAI LLM adapter for Ragas evaluation. | 내부 |
| `./src/evalvault/adapters/outbound/llm/base.py` | Python | code-backend | lens:개발;type:소스 | 포함 | - | 2026-01-28T17:55:07 | read-full | last:     return OpenAIEmbeddingsWithLegacy(model=model, client=client) | Python text file: Shared helpers for LLM adapters. | 내부 |
| `./src/evalvault/adapters/outbound/llm/factory.py` | Python | code-backend | lens:개발;type:소스 | 포함 | - | 2026-01-28T17:55:07 | read-full | last:     return None | Python text file: factory.py | 내부 |
| `./src/evalvault/adapters/outbound/llm/instructor_factory.py` | Python | code-backend | lens:개발;type:소스 | 포함 | - | 2026-01-28T17:55:07 | read-full | last:     ) | Python text file: instructor_factory.py | 내부 |
| `./src/evalvault/adapters/outbound/llm/llm_relation_augmenter.py` | Python | code-backend | lens:개발;type:소스 | 포함 | - | 2026-01-28T17:55:07 | read-full | last:         return data | Python text file: LLM-backed relation augmenter for knowledge graph generation. | 내부 |
| `./src/evalvault/adapters/outbound/llm/ollama_adapter.py` | Python | code-backend | lens:개발;type:소스 | 포함 | - | 2026-01-28T17:55:07 | read-full | last:             return asyncio.run(self.agenerate_text(prompt, options=options)) | Python text file: Ollama LLM adapter for air-gapped (폐쇄망) environments. | 내부 |
| `./src/evalvault/adapters/outbound/llm/openai_adapter.py` | Python | code-backend | lens:개발;type:소스 | 포함 | - | 2026-01-28T17:55:07 | read-full | last:         return content | Python text file: OpenAI LLM adapter for Ragas evaluation. | 내부 |
| `./src/evalvault/adapters/outbound/llm/token_aware_chat.py` | Python | code-backend | lens:개발;type:소스 | 포함 | - | 2026-01-28T17:55:07 | read-full | last:         return TrackingChat(self._original_chat, self._usage_tracker) | Python text file: Token tracking clients shared by LLM adapters. | 내부 |
| `./src/evalvault/adapters/outbound/llm/vllm_adapter.py` | Python | code-backend | lens:개발;type:소스 | 포함 | - | 2026-01-28T17:55:07 | read-full | last:         return content | Python text file: vLLM LLM adapter for OpenAI-compatible serving. | 내부 |
| `./src/evalvault/adapters/outbound/methods/__init__.py` | Python | code-backend | lens:개발;type:소스 | 포함 | - | 2026-01-28T17:55:07 | read-full | last: \] | Python text file: Method plugin adapters. | 내부 |
| `./src/evalvault/adapters/outbound/methods/baseline_oracle.py` | Python | code-backend | lens:개발;type:소스 | 포함 | - | 2026-01-28T17:55:07 | read-full | last:         return outputs | Python text file: Baseline method plugin that uses ground truth as the answer. | 내부 |
| `./src/evalvault/adapters/outbound/methods/external_command.py` | Python | code-backend | lens:개발;type:소스 | 포함 | - | 2026-01-28T17:55:07 | read-full | last:         return outputs | Python text file: External command method adapter for dependency isolation. | 내부 |
| `./src/evalvault/adapters/outbound/methods/registry.py` | Python | code-backend | lens:개발;type:소스 | 포함 | - | 2026-01-28T17:55:07 | read-full | last:         return f"{exc.__class__.__name__}: {first_line}" | Python text file: Registry for method plugins (internal config + entry points). | 내부 |
| `./src/evalvault/adapters/outbound/nlp/__init__.py` | Python | code-backend | lens:개발;type:소스 | 포함 | - | 2026-01-28T17:55:07 | read-full | last: """NLP adapters for text processing.""" | Python text file: NLP adapters for text processing. | 내부 |
| `./src/evalvault/adapters/outbound/nlp/korean/__init__.py` | Python | code-backend | lens:개발;type:소스 | 포함 | - | 2026-01-28T17:55:07 | read-full | last: \] | Python text file: Korean NLP adapters. | 내부 |
| `./src/evalvault/adapters/outbound/nlp/korean/bm25_retriever.py` | Python | code-backend | lens:개발;type:소스 | 포함 | - | 2026-01-28T17:55:07 | read-full | last:         logger.info("BM25 인덱스 초기화") | Python text file: Korean BM25 Retriever with morphological analysis. | 내부 |
| `./src/evalvault/adapters/outbound/nlp/korean/dense_retriever.py` | Python | code-backend | lens:개발;type:소스 | 포함 | - | 2026-01-28T17:55:07 | read-full | last:         logger.info("Dense 인덱스 초기화") | Python text file: Korean Dense Retriever with BGE-M3 and Qwen3-Embedding support. | 내부 |
| `./src/evalvault/adapters/outbound/nlp/korean/document_chunker.py` | Python | code-backend | lens:개발;type:소스 | 포함 | - | 2026-01-28T17:55:07 | read-full | last:         return chunks | Python text file: Korean document chunker with semantic awareness. | 내부 |
| `./src/evalvault/adapters/outbound/nlp/korean/hybrid_retriever.py` | Python | code-backend | lens:개발;type:소스 | 포함 | - | 2026-01-28T17:55:07 | read-full | last:         logger.info("하이브리드 인덱스 초기화") | Python text file: Korean Hybrid Retriever combining BM25 and Dense search. | 내부 |
| `./src/evalvault/adapters/outbound/nlp/korean/kiwi_tokenizer.py` | Python | code-backend | lens:개발;type:소스 | 포함 | - | 2026-01-28T17:55:07 | read-full | last:         logger.info(f"보험 용어 {len(terms)}개 추가") | Python text file: Kiwi 기반 한국어 토크나이저. | 내부 |
| `./src/evalvault/adapters/outbound/nlp/korean/korean_evaluation.py` | Python | code-backend | lens:개발;type:소스 | 포함 | - | 2026-01-28T17:55:07 | read-full | last:         return intersection / union if union > 0 else 0.0 | Python text file: Korean RAG Evaluation utilities. | 내부 |
| `./src/evalvault/adapters/outbound/nlp/korean/korean_stopwords.py` | Python | code-backend | lens:개발;type:소스 | 포함 | - | 2026-01-28T17:55:07 | read-full | last:     return pos_tag in KEYWORD_POS_TAGS | Python text file: 한국어 불용어 사전. | 내부 |
| `./src/evalvault/adapters/outbound/nlp/korean/toolkit.py` | Python | code-backend | lens:개발;type:소스 | 포함 | - | 2026-01-28T17:55:07 | read-full | last: __all__ = \["KoreanNLPToolkit"\] | Python text file: Korean NLP toolkit adapter implementing outbound ports. | 내부 |
| `./src/evalvault/adapters/outbound/nlp/korean/toolkit_factory.py` | Python | code-backend | lens:개발;type:소스 | 포함 | - | 2026-01-28T17:55:07 | read-full | last:         return None | Python text file: toolkit_factory.py | 내부 |
| `./src/evalvault/adapters/outbound/phoenix/sync_service.py` | Python | code-backend | lens:개발;type:소스 | 포함 | - | 2026-01-28T17:55:07 | read-full | last: \] | Python text file: Phoenix dataset / experiment synchronization helpers. | 내부 |
| `./src/evalvault/adapters/outbound/report/__init__.py` | Python | code-backend | lens:개발;type:소스 | 포함 | - | 2026-01-28T17:55:07 | read-full | last: \] | Python text file: Report generation adapters. | 내부 |
| `./src/evalvault/adapters/outbound/report/ci_report_formatter.py` | Python | code-backend | lens:개발;type:소스 | 포함 | - | 2026-01-28T17:55:07 | read-full | last: __all__ = \["CIGateMetricRow", "format_ci_regression_report"\] | Python text file: ci_report_formatter.py | 내부 |
| `./src/evalvault/adapters/outbound/report/dashboard_generator.py` | Python | code-backend | lens:개발;type:소스 | 포함 | - | 2026-01-28T17:55:07 | read-full | last:     return max(0.0, min(1.0, float(value))) | Python text file: dashboard_generator.py | 내부 |
| `./src/evalvault/adapters/outbound/report/llm_report_generator.py` | Python | code-backend | lens:개발;type:소스 | 포함 | - | 2026-01-28T17:55:07 | read-full | last:         ) | Python text file: LLM-powered intelligent report generator. | 내부 |
| `./src/evalvault/adapters/outbound/report/markdown_adapter.py` | Python | code-backend | lens:개발;type:소스 | 포함 | - | 2026-01-28T17:55:07 | read-full | last:         return html | Python text file: Markdown report generation adapter. | 내부 |
| `./src/evalvault/adapters/outbound/report/pr_comment_formatter.py` | Python | code-backend | lens:개발;type:소스 | 포함 | - | 2026-01-28T17:55:07 | read-full | last: __all__ = \["format_ci_gate_pr_comment"\] | Python text file: pr_comment_formatter.py | 내부 |
| `./src/evalvault/adapters/outbound/retriever/__init__.py` | Python | code-backend | lens:개발;type:소스 | 포함 | - | 2026-01-28T17:55:07 | read-full | last: __all__ = \["GraphRAGAdapter", "LightRAGGraphAdapter"\] | Python text file: Retriever adapters. | 내부 |
| `./src/evalvault/adapters/outbound/retriever/graph_rag_adapter.py` | Python | code-backend | lens:개발;type:소스 | 포함 | - | 2026-01-28T17:55:07 | read-full | last: __all__ = \["GraphRAGAdapter", "LightRAGGraphAdapter"\] | Python text file: GraphRAG adapter that exposes graph-centric retrieval helpers. | 내부 |
| `./src/evalvault/adapters/outbound/storage/__init__.py` | Python | code-backend | lens:개발;type:소스 | 포함 | - | 2026-01-28T17:55:07 | read-full | last:     __all__ = \["SQLiteStorageAdapter", "SQLiteBenchmarkStorageAdapter"\] | Python text file: Storage adapters for evaluation results. | 내부 |
| `./src/evalvault/adapters/outbound/storage/base_sql.py` | Python | code-backend | lens:개발;type:소스 | 포함 | - | 2026-01-28T17:55:07 | read-full | last:         return output | Python text file: Shared SQL storage helpers for multiple adapters. | 내부 |
| `./src/evalvault/adapters/outbound/storage/benchmark_storage_adapter.py` | Python | code-backend | lens:개발;type:소스 | 포함 | - | 2026-01-28T17:55:07 | read-full | last:         ) | Python text file: SQLite storage adapter for benchmark run persistence. | 내부 |
| `./src/evalvault/adapters/outbound/storage/postgres_adapter.py` | Python | code-backend | lens:개발;type:소스 | 포함 | - | 2026-01-28T17:55:07 | read-full | last:         return value | Python text file: PostgreSQL storage adapter for evaluation results. | 내부 |
| `./src/evalvault/adapters/outbound/storage/postgres_schema.sql` | SQL | code-backend | lens:개발;type:소스 | 포함 | - | 2026-01-28T17:55:07 | binary-scan | size: 11255 bytes | SQL binary file (11255 bytes) | 내부 |
| `./src/evalvault/adapters/outbound/storage/schema.sql` | SQL | code-backend | lens:개발;type:소스 | 포함 | - | 2026-01-28T17:55:07 | binary-scan | size: 13015 bytes | SQL binary file (13015 bytes) | 내부 |
| `./src/evalvault/adapters/outbound/storage/sqlite_adapter.py` | Python | code-backend | lens:개발;type:소스 | 포함 | - | 2026-01-28T17:55:07 | read-full | last:         return deleted | Python text file: SQLite storage adapter for evaluation results. | 내부 |
| `./src/evalvault/adapters/outbound/tracer/__init__.py` | Python | code-backend | lens:개발;type:소스 | 포함 | - | 2026-01-28T17:55:07 | read-full | last: \] | Python text file: Tracer adapters. | 내부 |
| `./src/evalvault/adapters/outbound/tracer/open_rag_log_handler.py` | Python | code-backend | lens:개발;type:소스 | 포함 | - | 2026-01-28T17:55:07 | read-full | last: __all__ = \["OpenRagLogHandler", "install_open_rag_log_handler"\] | Python text file: Open RAG Trace logging handler. | 내부 |
| `./src/evalvault/adapters/outbound/tracer/open_rag_trace_adapter.py` | Python | code-backend | lens:개발;type:소스 | 포함 | - | 2026-01-28T17:55:07 | read-full | last: __all__ = \["OpenRagTraceAdapter", "OpenRagTraceConfig"\] | Python text file: Open RAG Trace adapter using OpenTelemetry when available. | 내부 |
| `./src/evalvault/adapters/outbound/tracer/open_rag_trace_decorators.py` | Python | code-backend | lens:개발;type:소스 | 포함 | - | 2026-01-28T17:55:07 | read-full | last: __all__ = \["trace_module"\] | Python text file: Convenience decorators for Open RAG Trace spans. | 내부 |
| `./src/evalvault/adapters/outbound/tracer/open_rag_trace_helpers.py` | Python | code-backend | lens:개발;type:소스 | 포함 | - | 2026-01-28T17:55:07 | read-full | last: \] | Python text file: Helpers for building Open RAG Trace attributes. | 내부 |
| `./src/evalvault/adapters/outbound/tracer/phoenix_tracer_adapter.py` | Python | code-backend | lens:개발;type:소스 | 포함 | - | 2026-01-28T17:55:07 | read-full | last:         set_span_attributes(span, attributes) | Python text file: Phoenix/OpenTelemetry tracer adapter. | 내부 |
| `./src/evalvault/adapters/outbound/tracker/__init__.py` | Python | code-backend | lens:개발;type:소스 | 포함 | - | 2026-01-28T17:55:07 | read-full | last: __all__ = \["LangfuseAdapter", "MLflowAdapter", "PhoenixAdapter"\] | Python text file: Tracker adapters for logging evaluation traces. | 내부 |
| `./src/evalvault/adapters/outbound/tracker/langfuse_adapter.py` | Python | code-backend | lens:개발;type:소스 | 포함 | - | 2026-01-28T17:55:07 | read-full | last:         run.langfuse_trace_id = trace_id | Python text file: Langfuse tracker adapter implementation. | 내부 |
| `./src/evalvault/adapters/outbound/tracker/log_sanitizer.py` | Python | code-backend | lens:개발;type:소스 | 포함 | - | 2026-01-28T17:55:07 | read-full | last:     return sanitize_text(str(value), max_chars=max_chars) | Python text file: log_sanitizer.py | 내부 |
| `./src/evalvault/adapters/outbound/tracker/mlflow_adapter.py` | Python | code-backend | lens:개발;type:소스 | 포함 | - | 2026-01-28T17:55:07 | read-full | last:         return trace_id | Python text file: MLflow tracker adapter implementation. | 내부 |
| `./src/evalvault/adapters/outbound/tracker/phoenix_adapter.py` | Python | code-backend | lens:개발;type:소스 | 포함 | - | 2026-01-28T17:55:07 | read-full | last:     return doc_ids | Python text file: Phoenix tracker adapter implementation using OpenTelemetry. | 내부 |
| `./src/evalvault/config/__init__.py` | Python | code-backend | lens:개발;type:소스 | 포함 | - | 2026-01-28T17:55:07 | read-full | last: \] | Python text file: Configuration module. | 내부 |
| `./src/evalvault/config/agent_types.py` | Python | code-backend | lens:개발;type:소스 | 포함 | - | 2026-01-28T17:55:07 | read-full | last:     \] | Python text file: Agent Types and Configuration | 내부 |
| `./src/evalvault/config/domain_config.py` | Python | code-backend | lens:개발;type:소스 | 포함 | - | 2026-01-28T17:55:07 | read-full | last:     return config_path | Python text file: Domain Memory configuration module. | 내부 |
| `./src/evalvault/config/instrumentation.py` | Python | code-backend | lens:개발;type:소스 | 포함 | - | 2026-01-28T17:55:07 | read-full | last:     return _tracer_provider | Python text file: Phoenix instrumentation setup for automatic LLM tracing. | 내부 |
| `./src/evalvault/config/langfuse_support.py` | Python | code-backend | lens:개발;type:소스 | 포함 | - | 2026-01-28T17:55:07 | read-full | last:     return None | Python text file: Helpers for Langfuse metadata extraction. | 내부 |
| `./src/evalvault/config/model_config.py` | Python | code-backend | lens:개발;type:소스 | 포함 | - | 2026-01-28T17:55:07 | read-full | last:     _model_config = None | Python text file: Model configuration with YAML profiles support. | 내부 |
| `./src/evalvault/config/phoenix_support.py` | Python | code-backend | lens:개발;type:소스 | 포함 | - | 2026-01-28T17:55:07 | read-full | last: \] | Python text file: Helpers for enabling Phoenix instrumentation across CLI commands. | 내부 |
| `./src/evalvault/config/playbooks/improvement_playbook.yaml` | YAML | code-backend | lens:개발;type:소스 | 포함 | - | 2026-01-28T17:55:07 | read-full | last:   gate: "evalvault gate results.json --threshold {metric}:{threshold}" | YAML text file: improvement_playbook.yaml | 내부 |
| `./src/evalvault/config/secret_manager.py` | Python | code-backend | lens:개발;type:소스 | 포함 | - | 2026-01-28T17:55:07 | read-full | last:     return secret_value | Python text file: secret_manager.py | 내부 |
| `./src/evalvault/config/settings.py` | Python | code-backend | lens:개발;type:소스 | 포함 | - | 2026-01-28T17:55:07 | read-full | last: settings = get_settings() | Python text file: Application settings using pydantic-settings. | 내부 |
| `./src/evalvault/debug_ragas.py` | Python | code-backend | lens:개발;type:소스 | 포함 | - | 2026-01-28T17:55:07 | read-full | last:     asyncio.run(debug_ragas()) | Python text file: debug_ragas.py | 내부 |
| `./src/evalvault/debug_ragas_real.py` | Python | code-backend | lens:개발;type:소스 | 포함 | - | 2026-01-28T17:55:07 | read-full | last:     asyncio.run(debug_ragas_real()) | Python text file: debug_ragas_real.py | 내부 |
| `./src/evalvault/domain/__init__.py` | Python | code-backend | lens:개발;type:소스 | 포함 | - | 2026-01-28T17:55:07 | read-full | last: (empty) | Python text file: __init__.py | 내부 |
| `./src/evalvault/domain/entities/__init__.py` | Python | code-backend | lens:개발;type:소스 | 포함 | - | 2026-01-28T17:55:07 | read-full | last: \] | Python text file: Domain entities. | 내부 |
| `./src/evalvault/domain/entities/analysis.py` | Python | code-backend | lens:개발;type:소스 | 포함 | - | 2026-01-28T17:55:07 | read-full | last:         return \[fi for fi in self.factor_impacts if fi.factor_type == factor_type\] | Python text file: Analysis result entities for statistical, NLP, and causal analysis. | 내부 |
| `./src/evalvault/domain/entities/analysis_pipeline.py` | Python | code-backend | lens:개발;type:소스 | 포함 | - | 2026-01-28T17:55:07 | read-full | last:                 self._collect_dependencies(dep_id, collected) | Python text file: Phase 14: Query-Based DAG Analysis Pipeline Entities. | 내부 |
| `./src/evalvault/domain/entities/benchmark.py` | Python | code-backend | lens:개발;type:소스 | 포함 | - | 2026-01-28T17:55:07 | read-full | last:     return uuid.uuid4().hex\[:16\] | Python text file: Benchmark entities with multi-framework compatibility. | 내부 |
| `./src/evalvault/domain/entities/benchmark_run.py` | Python | code-backend | lens:개발;type:소스 | 포함 | - | 2026-01-28T17:55:07 | read-full | last:         ) | Python text file: Benchmark run domain entity for storing benchmark evaluation results. | 내부 |
| `./src/evalvault/domain/entities/dataset.py` | Python | code-backend | lens:개발;type:소스 | 포함 | - | 2026-01-28T17:55:07 | read-full | last:         return \[tc.to_ragas_dict() for tc in self.test_cases\] | Python text file: Dataset entities for RAG evaluation. | 내부 |
| `./src/evalvault/domain/entities/debug.py` | Python | code-backend | lens:개발;type:소스 | 포함 | - | 2026-01-28T17:55:07 | read-full | last:         } | Python text file: Debug report entities. | 내부 |
| `./src/evalvault/domain/entities/experiment.py` | Python | code-backend | lens:개발;type:소스 | 포함 | - | 2026-01-28T17:55:07 | read-full | last:         raise ValueError(f"Group not found: {group_name}") | Python text file: Experiment entity for A/B testing and experiment management. | 내부 |
| `./src/evalvault/domain/entities/feedback.py` | Python | code-backend | lens:개발;type:소스 | 포함 | - | 2026-01-28T17:55:07 | read-full | last:     cases: dict\[str, CalibrationCaseResult\] = field(default_factory=dict) | Python text file: feedback.py | 내부 |
| `./src/evalvault/domain/entities/graph_rag.py` | Python | code-backend | lens:개발;type:소스 | 포함 | - | 2026-01-28T17:55:07 | read-full | last:     relevance_score: float | Python text file: graph_rag.py | 내부 |
| `./src/evalvault/domain/entities/improvement.py` | Python | code-backend | lens:개발;type:소스 | 포함 | - | 2026-01-28T17:55:07 | read-full | last:         return "\n".join(lines) | Python text file: RAG Improvement Guide entities. | 내부 |
| `./src/evalvault/domain/entities/judge_calibration.py` | Python | code-backend | lens:개발;type:소스 | 포함 | - | 2026-01-28T17:55:07 | read-full | last:     warnings: list\[str\] = field(default_factory=list) | Python text file: judge_calibration.py | 내부 |
| `./src/evalvault/domain/entities/kg.py` | Python | code-backend | lens:개발;type:소스 | 포함 | - | 2026-01-28T17:55:07 | read-full | last:         } | Python text file: Pydantic models for knowledge graph entities and relations. | 내부 |
| `./src/evalvault/domain/entities/memory.py` | Python | code-backend | lens:개발;type:소스 | 포함 | - | 2026-01-28T17:55:07 | read-full | last:         return sorted(self.behaviors, key=lambda b: b.success_rate, reverse=True)\[:n\] | Python text file: Domain memory entities for factual, experiential, and working memory layers. | 내부 |
| `./src/evalvault/domain/entities/method.py` | Python | code-backend | lens:개발;type:소스 | 포함 | - | 2026-01-28T17:55:07 | read-full | last:         return iter(self.test_cases) | Python text file: Method plugin entities for the evaluation testbed. | 내부 |
| `./src/evalvault/domain/entities/multiturn.py` | Python | code-backend | lens:개발;type:소스 | 포함 | - | 2026-01-28T17:55:07 | read-full | last:     summary: dict\[str, Any\] = field(default_factory=dict) | Python text file: multiturn.py | 내부 |
| `./src/evalvault/domain/entities/prompt.py` | Python | code-backend | lens:개발;type:소스 | 포함 | - | 2026-01-28T17:55:07 | read-full | last:         } | Python text file: Prompt entities for tracking system and Ragas prompts. | 내부 |
| `./src/evalvault/domain/entities/prompt_suggestion.py` | Python | code-backend | lens:개발;type:소스 | 포함 | - | 2026-01-28T17:55:07 | read-full | last:     metadata: dict\[str, Any\] = field(default_factory=dict) | Python text file: Prompt suggestion entities. | 내부 |
| `./src/evalvault/domain/entities/rag_trace.py` | Python | code-backend | lens:개발;type:소스 | 포함 | - | 2026-01-28T17:55:07 | read-full | last:         return attrs | Python text file: RAG trace data entities for observability. | 내부 |
| `./src/evalvault/domain/entities/result.py` | Python | code-backend | lens:개발;type:소스 | 포함 | - | 2026-01-28T17:55:07 | read-full | last:     created_at: datetime \| None = None | Python text file: Evaluation result entities. | 내부 |
| `./src/evalvault/domain/entities/stage.py` | Python | code-backend | lens:개발;type:소스 | 포함 | - | 2026-01-28T17:55:07 | read-full | last:     return float(value) | Python text file: Stage-level trace entities for RAG pipelines. | 내부 |
| `./src/evalvault/domain/metrics/__init__.py` | Python | code-backend | lens:개발;type:소스 | 포함 | - | 2026-01-28T17:55:07 | read-full | last: \] | Python text file: Custom domain-specific metrics for RAG evaluation. | 내부 |
| `./src/evalvault/domain/metrics/analysis_registry.py` | Python | code-backend | lens:개발;type:소스 | 포함 | - | 2026-01-28T17:55:07 | read-full | last:     return \[spec.key for spec in _ANALYSIS_METRICS\] | Python text file: Analysis metric registry for pipeline outputs. | 내부 |
| `./src/evalvault/domain/metrics/confidence.py` | Python | code-backend | lens:개발;type:소스 | 포함 | - | 2026-01-28T17:55:07 | read-full | last:         return confidence < threshold | Python text file: Confidence Score metric for RAG evaluation. | 내부 |
| `./src/evalvault/domain/metrics/contextual_relevancy.py` | Python | code-backend | lens:개발;type:소스 | 포함 | - | 2026-01-28T17:55:07 | read-full | last:         return results | Python text file: Contextual Relevancy metric for RAG evaluation. | 내부 |
| `./src/evalvault/domain/metrics/entity_preservation.py` | Python | code-backend | lens:개발;type:소스 | 포함 | - | 2026-01-28T17:55:07 | read-full | last:         return format(value.normalize(), "f").rstrip("0").rstrip(".") | Python text file: Entity preservation metric for summarization in insurance domain. | 내부 |
| `./src/evalvault/domain/metrics/insurance.py` | Python | code-backend | lens:개발;type:소스 | 포함 | - | 2026-01-28T17:55:07 | read-full | last:         return self._calculate_accuracy(answer, contexts) | Python text file: Insurance domain-specific evaluation metrics. | 내부 |
| `./src/evalvault/domain/metrics/multiturn_metrics.py` | Python | code-backend | lens:개발;type:소스 | 포함 | - | 2026-01-28T17:55:07 | read-full | last:     return values\[lower\] + (values\[upper\] - values\[lower\]) * fraction | Python text file: Utilities for multi-turn evaluation metrics. | 내부 |
| `./src/evalvault/domain/metrics/no_answer.py` | Python | code-backend | lens:개발;type:소스 | 포함 | - | 2026-01-28T17:55:07 | read-full | last:     return _is_no_answer(text) | Python text file: No-answer accuracy metric for RAG evaluation. | 내부 |
| `./src/evalvault/domain/metrics/registry.py` | Python | code-backend | lens:개발;type:소스 | 포함 | - | 2026-01-28T17:55:07 | read-full | last:     return {spec.name: spec for spec in _METRIC_SPECS} | Python text file: Metric registry for CLI/Web UI integrations. | 내부 |
| `./src/evalvault/domain/metrics/retrieval_rank.py` | Python | code-backend | lens:개발;type:소스 | 포함 | - | 2026-01-28T17:55:07 | read-full | last:         } | Python text file: Retrieval ranking metrics for RAG evaluation. | 내부 |
| `./src/evalvault/domain/metrics/summary_accuracy.py` | Python | code-backend | lens:개발;type:소스 | 포함 | - | 2026-01-28T17:55:07 | read-full | last:         return format(value.normalize(), "f").rstrip("0").rstrip(".") | Python text file: summary_accuracy.py | 내부 |
| `./src/evalvault/domain/metrics/summary_needs_followup.py` | Python | code-backend | lens:개발;type:소스 | 포함 | - | 2026-01-28T17:55:07 | read-full | last:         ) | Python text file: summary_needs_followup.py | 내부 |
| `./src/evalvault/domain/metrics/summary_non_definitive.py` | Python | code-backend | lens:개발;type:소스 | 포함 | - | 2026-01-28T17:55:07 | read-full | last:         return any(re.search(pattern, lowered) for pattern in self._DEFINITIVE_PATTERNS_EN) | Python text file: summary_non_definitive.py | 내부 |
| `./src/evalvault/domain/metrics/summary_risk_coverage.py` | Python | code-backend | lens:개발;type:소스 | 포함 | - | 2026-01-28T17:55:07 | read-full | last:         return any(keyword in text or keyword.lower() in lowered for keyword in keywords) | Python text file: summary_risk_coverage.py | 내부 |
| `./src/evalvault/domain/metrics/terms_dictionary.json` | JSON | code-backend | lens:개발;type:소스 | 포함 | - | 2026-01-28T17:55:07 | read-full | keys: 보험금,보험료,피보험자,보험계약자,보험수익자,면책기간,보장내용,해지환급금,보험가입금액,특약,주계약,갱신; last: } | JSON object with 20 keys | 내부 |
| `./src/evalvault/domain/metrics/text_match.py` | Python | code-backend | lens:개발;type:소스 | 포함 | - | 2026-01-28T17:55:07 | read-full | last:         } | Python text file: Text matching metrics for RAG evaluation. | 내부 |
| `./src/evalvault/domain/services/__init__.py` | Python | code-backend | lens:개발;type:소스 | 포함 | - | 2026-01-28T17:55:07 | read-full | last: \] | Python text file: Domain services. | 내부 |
| `./src/evalvault/domain/services/analysis_service.py` | Python | code-backend | lens:개발;type:소스 | 포함 | - | 2026-01-28T17:55:07 | read-full | last:         return recommendations | Python text file: 분석 서비스. | 내부 |
| `./src/evalvault/domain/services/artifact_lint_service.py` | Python | code-backend | lens:개발;type:소스 | 포함 | - | 2026-01-28T17:55:07 | read-full | last:     return "ok" | Python text file: artifact_lint_service.py | 내부 |
| `./src/evalvault/domain/services/async_batch_executor.py` | Python | code-backend | lens:개발;type:소스 | 포함 | - | 2026-01-28T17:55:07 | read-full | last: \] | Python text file: 향상된 비동기 배치 실행기. | 내부 |
| `./src/evalvault/domain/services/batch_executor.py` | Python | code-backend | lens:개발;type:소스 | 포함 | - | 2026-01-28T17:55:07 | read-full | last: __all__ = \["chunked", "run_in_batches"\] | Python text file: Async batching helpers for evaluator performance. | 내부 |
| `./src/evalvault/domain/services/benchmark_report_service.py` | Python | code-backend | lens:개발;type:소스 | 포함 | - | 2026-01-28T17:55:07 | read-full | last:         return asyncio.run(self.generate_trend_report(benchmark_runs)) | Python text file: Benchmark Report Service. | 내부 |
| `./src/evalvault/domain/services/benchmark_runner.py` | Python | code-backend | lens:개발;type:소스 | 포함 | - | 2026-01-28T17:55:07 | read-full | last:     return _run_benchmarks | Python text file: Korean RAG Benchmark Runner. | 내부 |
| `./src/evalvault/domain/services/benchmark_service.py` | Python | code-backend | lens:개발;type:소스 | 포함 | - | 2026-01-28T17:55:07 | read-full | last:         ) | Python text file: Benchmark orchestration service following hexagonal architecture. | 내부 |
| `./src/evalvault/domain/services/cache_metrics.py` | Python | code-backend | lens:개발;type:소스 | 포함 | - | 2026-01-28T17:55:07 | read-full | last: __all__ = \["CacheMetricsWindow", "CacheStatsSnapshot", "CacheStatsTracker"\] | Python text file: Cache metrics helpers. | 내부 |
| `./src/evalvault/domain/services/cluster_map_builder.py` | Python | code-backend | lens:개발;type:소스 | 포함 | - | 2026-01-28T17:55:07 | read-full | last:     ) | Python text file: Cluster map generation utilities. | 내부 |
| `./src/evalvault/domain/services/custom_metric_snapshot.py` | Python | code-backend | lens:개발;type:소스 | 포함 | - | 2026-01-28T17:55:07 | read-full | last:     return {"schema_version": SCHEMA_VERSION, "metrics": rows} | Python text file: custom_metric_snapshot.py | 내부 |
| `./src/evalvault/domain/services/dataset_preprocessor.py` | Python | code-backend | lens:개발;type:소스 | 포함 | - | 2026-01-28T17:55:07 | read-full | last:         return True | Python text file: Dataset preprocessing guardrails for RAG evaluation. | 내부 |
| `./src/evalvault/domain/services/debug_report_service.py` | Python | code-backend | lens:개발;type:소스 | 포함 | - | 2026-01-28T17:55:07 | read-full | last:         return recommendations | Python text file: Debug report service. | 내부 |
| `./src/evalvault/domain/services/difficulty_profile_reporter.py` | Python | code-backend | lens:개발;type:소스 | 포함 | - | 2026-01-28T17:55:07 | read-full | last:         ) | Python text file: difficulty_profile_reporter.py | 내부 |
| `./src/evalvault/domain/services/difficulty_profiling_service.py` | Python | code-backend | lens:개발;type:소스 | 포함 | - | 2026-01-28T17:55:07 | read-full | last:     } | Python text file: difficulty_profiling_service.py | 내부 |
| `./src/evalvault/domain/services/document_chunker.py` | Python | code-backend | lens:개발;type:소스 | 포함 | - | 2026-01-28T17:55:07 | read-full | last:         return chunks | Python text file: Document chunking utilities for testset generation. | 내부 |
| `./src/evalvault/domain/services/document_versioning.py` | Python | code-backend | lens:개발;type:소스 | 포함 | - | 2026-01-28T17:55:07 | read-full | last:     return selected | Python text file: document_versioning.py | 내부 |
| `./src/evalvault/domain/services/domain_learning_hook.py` | Python | code-backend | lens:개발;type:소스 | 포함 | - | 2026-01-28T17:55:07 | read-full | last:         } | Python text file: Domain Learning Hook service. | 내부 |
| `./src/evalvault/domain/services/embedding_overlay.py` | Python | code-backend | lens:개발;type:소스 | 포함 | - | 2026-01-28T17:55:07 | read-full | last: __all__ = \["build_cluster_facts"\] | Python text file: Utilities for converting Phoenix embedding exports into Domain Memory facts. | 내부 |
| `./src/evalvault/domain/services/entity_extractor.py` | Python | code-backend | lens:개발;type:소스 | 포함 | - | 2026-01-28T17:55:07 | read-full | last:         return relations | Python text file: Entity and relation extraction for knowledge graph construction. | 내부 |
| `./src/evalvault/domain/services/evaluator.py` | Python | code-backend | lens:개발;type:소스 | 포함 | - | 2026-01-28T17:55:07 | read-full | last:         return cost | Python text file: Ragas evaluation service. | 내부 |
| `./src/evalvault/domain/services/experiment_comparator.py` | Python | code-backend | lens:개발;type:소스 | 포함 | - | 2026-01-28T17:55:07 | read-full | last: __all__ = \["ExperimentComparator", "MetricComparison"\] | Python text file: Utilities for comparing experiment groups. | 내부 |
| `./src/evalvault/domain/services/experiment_manager.py` | Python | code-backend | lens:개발;type:소스 | 포함 | - | 2026-01-28T17:55:07 | read-full | last: __all__ = \["ExperimentManager", "MetricComparison"\] | Python text file: Experiment management service for A/B testing and metric comparison. | 내부 |
| `./src/evalvault/domain/services/experiment_reporter.py` | Python | code-backend | lens:개발;type:소스 | 포함 | - | 2026-01-28T17:55:07 | read-full | last:         } | Python text file: Generate experiment reports that combine statistics and comparisons. | 내부 |
| `./src/evalvault/domain/services/experiment_repository.py` | Python | code-backend | lens:개발;type:소스 | 포함 | - | 2026-01-28T17:55:07 | read-full | last:         return experiment | Python text file: Storage-facing helper for Experiment entities. | 내부 |
| `./src/evalvault/domain/services/experiment_statistics.py` | Python | code-backend | lens:개발;type:소스 | 포함 | - | 2026-01-28T17:55:07 | read-full | last:         } | Python text file: Summary helpers for experiments. | 내부 |
| `./src/evalvault/domain/services/graph_rag_experiment.py` | Python | code-backend | lens:개발;type:소스 | 포함 | - | 2026-01-28T17:55:07 | read-full | last: __all__ = \["GraphRAGExperiment", "GraphRAGExperimentResult"\] | Python text file: GraphRAG experiment helper for baseline vs graph comparison. | 내부 |
| `./src/evalvault/domain/services/holdout_splitter.py` | Python | code-backend | lens:개발;type:소스 | 포함 | - | 2026-01-28T17:55:07 | read-full | last:     ) | Python text file: holdout_splitter.py | 내부 |
| `./src/evalvault/domain/services/improvement_guide_service.py` | Python | code-backend | lens:개발;type:소스 | 포함 | - | 2026-01-28T17:55:07 | read-full | last:     } | Python text file: Improvement Guide Service. | 내부 |
| `./src/evalvault/domain/services/intent_classifier.py` | Python | code-backend | lens:개발;type:소스 | 포함 | - | 2026-01-28T17:55:07 | read-full | last:         return found_keywords | Python text file: Phase 14.2: Intent Classifier Service. | 내부 |
| `./src/evalvault/domain/services/judge_calibration_service.py` | Python | code-backend | lens:개발;type:소스 | 포함 | - | 2026-01-28T17:55:07 | read-full | last:         return rng | Python text file: judge_calibration_service.py | 내부 |
| `./src/evalvault/domain/services/kg_generator.py` | Python | code-backend | lens:개발;type:소스 | 포함 | - | 2026-01-28T17:55:07 | read-full | last:         return list(best.values()) | Python text file: Knowledge graph-based testset generation. | 내부 |
| `./src/evalvault/domain/services/memory_aware_evaluator.py` | Python | code-backend | lens:개발;type:소스 | 포함 | - | 2026-01-28T17:55:07 | read-full | last:         return self._evaluator | Python text file: Memory-aware evaluation helpers that leverage Domain Memory. | 내부 |
| `./src/evalvault/domain/services/memory_based_analysis.py` | Python | code-backend | lens:개발;type:소스 | 포함 | - | 2026-01-28T17:55:07 | read-full | last:         return recommendations | Python text file: Memory-driven analysis utilities. | 내부 |
| `./src/evalvault/domain/services/method_runner.py` | Python | code-backend | lens:개발;type:소스 | 포함 | - | 2026-01-28T17:55:07 | read-full | last:         ) | Python text file: Service for running method plugins against base datasets. | 내부 |
| `./src/evalvault/domain/services/multiturn_evaluator.py` | Python | code-backend | lens:개발;type:소스 | 포함 | - | 2026-01-28T17:55:07 | read-full | last:         return dataset, mappings | Python text file: multiturn_evaluator.py | 내부 |
| `./src/evalvault/domain/services/ops_snapshot_service.py` | Python | code-backend | lens:개발;type:소스 | 포함 | - | 2026-01-28T17:55:07 | read-full | last:     } | Python text file: ops_snapshot_service.py | 내부 |
| `./src/evalvault/domain/services/pipeline_orchestrator.py` | Python | code-backend | lens:개발;type:소스 | 포함 | - | 2026-01-28T17:55:07 | read-full | last:         return self._orchestrator.list_registered_modules() | Python text file: Phase 14.3: Pipeline Orchestrator. | 내부 |
| `./src/evalvault/domain/services/pipeline_template_registry.py` | Python | code-backend | lens:개발;type:소스 | 포함 | - | 2026-01-28T17:55:07 | read-full | last:         ) | Python text file: Phase 14.2: Pipeline Template Registry. | 내부 |
| `./src/evalvault/domain/services/prompt_candidate_service.py` | Python | code-backend | lens:개발;type:소스 | 포함 | - | 2026-01-28T17:55:07 | read-full | last:         return variants + extra | Python text file: Candidate collection service for prompt suggestions. | 내부 |
| `./src/evalvault/domain/services/prompt_manifest.py` | Python | code-backend | lens:개발;type:소스 | 포함 | - | 2026-01-28T17:55:07 | read-full | last: \] | Python text file: Helper utilities for tracking Phoenix prompt versions. | 내부 |
| `./src/evalvault/domain/services/prompt_registry.py` | Python | code-backend | lens:개발;type:소스 | 포함 | - | 2026-01-28T17:55:07 | read-full | last:     return prompt_inputs | Python text file: Prompt set helpers for storing system/Ragas prompt snapshots. | 내부 |
| `./src/evalvault/domain/services/prompt_scoring_service.py` | Python | code-backend | lens:개발;type:소스 | 포함 | - | 2026-01-28T17:55:07 | read-full | last:     ) | Python text file: prompt_scoring_service.py | 내부 |
| `./src/evalvault/domain/services/prompt_status.py` | Python | code-backend | lens:개발;type:소스 | 포함 | - | 2026-01-28T17:55:07 | read-full | last: \] | Python text file: Formatting helpers for Phoenix prompt metadata surfaces. | 내부 |
| `./src/evalvault/domain/services/prompt_suggestion_reporter.py` | Python | code-backend | lens:개발;type:소스 | 포함 | - | 2026-01-28T17:55:07 | read-full | last:         } | Python text file: prompt_suggestion_reporter.py | 내부 |
| `./src/evalvault/domain/services/ragas_prompt_overrides.py` | Python | code-backend | lens:개발;type:소스 | 포함 | - | 2026-01-28T17:55:07 | read-full | last:     return normalize_ragas_prompt_overrides(content) | Python text file: Ragas prompt override parsing helpers. | 내부 |
| `./src/evalvault/domain/services/regression_gate_service.py` | Python | code-backend | lens:개발;type:소스 | 포함 | - | 2026-01-28T17:55:07 | read-full | last: \] | Python text file: Regression gate service for CLI automation. | 내부 |
| `./src/evalvault/domain/services/retrieval_metrics.py` | Python | code-backend | lens:개발;type:소스 | 포함 | - | 2026-01-28T17:55:07 | read-full | last:     return dcg / idcg | Python text file: Retrieval metric utilities for benchmark evaluations. | 내부 |
| `./src/evalvault/domain/services/retriever_context.py` | Python | code-backend | lens:개발;type:소스 | 포함 | - | 2026-01-28T17:55:07 | read-full | last:     return retrieval_metadata | Python text file: Utilities for applying retrievers to datasets. | 내부 |
| `./src/evalvault/domain/services/run_comparison_service.py` | Python | code-backend | lens:개발;type:소스 | 포함 | - | 2026-01-28T17:55:07 | read-full | last: \] | Python text file: run_comparison_service.py | 내부 |
| `./src/evalvault/domain/services/satisfaction_calibration_service.py` | Python | code-backend | lens:개발;type:소스 | 포함 | - | 2026-01-28T17:55:07 | read-full | last:             return None | Python text file: satisfaction_calibration_service.py | 내부 |
| `./src/evalvault/domain/services/stage_event_builder.py` | Python | code-backend | lens:개발;type:소스 | 포함 | - | 2026-01-28T17:55:07 | read-full | last:     return str(value) | Python text file: Stage event builder for evaluation runs. | 내부 |
| `./src/evalvault/domain/services/stage_metric_guide_service.py` | Python | code-backend | lens:개발;type:소스 | 포함 | - | 2026-01-28T17:56:20 | read-full | last:     return EffortLevel.MEDIUM | Python text file: Stage metric based improvement guide builder. | 내부 |
| `./src/evalvault/domain/services/stage_metric_service.py` | Python | code-backend | lens:개발;type:소스 | 포함 | - | 2026-01-28T17:56:20 | read-full | last:     return resolved | Python text file: Stage metric computation service. | 내부 |
| `./src/evalvault/domain/services/stage_summary_service.py` | Python | code-backend | lens:개발;type:소스 | 포함 | - | 2026-01-28T17:56:20 | read-full | last:         ) | Python text file: Stage summary service for pipeline observability. | 내부 |
| `./src/evalvault/domain/services/synthetic_qa_generator.py` | Python | code-backend | lens:개발;type:소스 | 포함 | - | 2026-01-28T17:56:20 | read-full | last:         ) | Python text file: Synthetic Q&A generation using LLM. | 내부 |
| `./src/evalvault/domain/services/testset_generator.py` | Python | code-backend | lens:개발;type:소스 | 포함 | - | 2026-01-28T17:56:20 | read-full | last:         ) | Python text file: Basic testset generation from documents. | 내부 |
| `./src/evalvault/domain/services/threshold_profiles.py` | Python | code-backend | lens:개발;type:소스 | 포함 | - | 2026-01-28T17:56:20 | read-full | last:     return resolved | Python text file: Threshold profile helpers for evaluation metrics. | 내부 |
| `./src/evalvault/domain/services/unified_report_service.py` | Python | code-backend | lens:개발;type:소스 | 포함 | - | 2026-01-28T17:56:20 | read-full | last:         return asyncio.run(self.generate_unified_report(eval_run, benchmark_run)) | Python text file: Unified Report Service. | 내부 |
| `./src/evalvault/domain/services/visual_space_service.py` | Python | code-backend | lens:개발;type:소스 | 포함 | - | 2026-01-28T17:56:20 | read-full | last:     } | Python text file: Build quadrant/3D visualization coordinates for evaluation runs. | 내부 |
| `./src/evalvault/mkdocs_helpers.py` | Python | code-backend | lens:개발;type:소스 | 포함 | - | 2026-01-28T17:56:20 | read-full | last:     return _slugify(value, separator) | Python text file: MkDocs helpers for documentation build. | 내부 |
| `./src/evalvault/ports/__init__.py` | Python | code-backend | lens:개발;type:소스 | 포함 | - | 2026-01-28T17:56:20 | read-full | last: (empty) | Python text file: __init__.py | 내부 |
| `./src/evalvault/ports/inbound/__init__.py` | Python | code-backend | lens:개발;type:소스 | 포함 | - | 2026-01-28T17:56:20 | read-full | last: \] | Python text file: Inbound ports. | 내부 |
| `./src/evalvault/ports/inbound/analysis_pipeline_port.py` | Python | code-backend | lens:개발;type:소스 | 포함 | - | 2026-01-28T17:56:20 | read-full | last:         ... | Python text file: Phase 14: Analysis Pipeline Port (Inbound). | 내부 |
| `./src/evalvault/ports/inbound/evaluator_port.py` | Python | code-backend | lens:개발;type:소스 | 포함 | - | 2026-01-28T17:56:20 | read-full | last:         ... | Python text file: 평가 실행 인터페이스. | 내부 |
| `./src/evalvault/ports/inbound/learning_hook_port.py` | Python | code-backend | lens:개발;type:소스 | 포함 | - | 2026-01-28T17:56:20 | read-full | last:         ... | Python text file: Domain Learning Hook port interface. | 내부 |
| `./src/evalvault/ports/inbound/multiturn_port.py` | Python | code-backend | lens:개발;type:소스 | 포함 | - | 2026-01-28T17:56:20 | read-full | last:     ) -> DriftAnalysis: ... | Python text file: multiturn_port.py | 내부 |
| `./src/evalvault/ports/inbound/web_port.py` | Python | code-backend | lens:개발;type:소스 | 포함 | - | 2026-01-28T17:56:20 | read-full | last:         ... | Python text file: Web UI inbound port interface. | 내부 |
| `./src/evalvault/ports/outbound/__init__.py` | Python | code-backend | lens:개발;type:소스 | 포함 | - | 2026-01-28T17:56:20 | read-full | last: \] | Python text file: Outbound ports. | 내부 |
| `./src/evalvault/ports/outbound/analysis_cache_port.py` | Python | code-backend | lens:개발;type:소스 | 포함 | - | 2026-01-28T17:56:20 | read-full | last:         ... | Python text file: 분석 결과 캐싱 인터페이스. | 내부 |
| `./src/evalvault/ports/outbound/analysis_module_port.py` | Python | code-backend | lens:개발;type:소스 | 포함 | - | 2026-01-28T17:56:20 | read-full | last:         ... | Python text file: Phase 14: Analysis Module Port (Outbound). | 내부 |
| `./src/evalvault/ports/outbound/analysis_port.py` | Python | code-backend | lens:개발;type:소스 | 포함 | - | 2026-01-28T17:56:20 | read-full | last:         ... | Python text file: 분석 서비스 인터페이스. | 내부 |
| `./src/evalvault/ports/outbound/artifact_fs_port.py` | Python | code-backend | lens:개발;type:소스 | 포함 | - | 2026-01-28T17:56:20 | read-full | last:     def read_text(self, path: Path) -> str: ... | Python text file: artifact_fs_port.py | 내부 |
| `./src/evalvault/ports/outbound/benchmark_port.py` | Python | code-backend | lens:개발;type:소스 | 포함 | - | 2026-01-28T17:56:20 | read-full | last:         pass | Python text file: Benchmark adapter port for external benchmark frameworks. | 내부 |
| `./src/evalvault/ports/outbound/causal_analysis_port.py` | Python | code-backend | lens:개발;type:소스 | 포함 | - | 2026-01-28T17:56:20 | read-full | last:         ... | Python text file: Causal analysis port interface. | 내부 |
| `./src/evalvault/ports/outbound/comparison_pipeline_port.py` | Python | code-backend | lens:개발;type:소스 | 포함 | - | 2026-01-28T17:56:20 | read-full | last: __all__ = \["ComparisonPipelinePort"\] | Python text file: comparison_pipeline_port.py | 내부 |
| `./src/evalvault/ports/outbound/dataset_port.py` | Python | code-backend | lens:개발;type:소스 | 포함 | - | 2026-01-28T17:56:20 | read-full | last:         ... | Python text file: 데이터셋 로드 인터페이스. | 내부 |
| `./src/evalvault/ports/outbound/difficulty_profile_port.py` | Python | code-backend | lens:개발;type:소스 | 포함 | - | 2026-01-28T17:56:20 | read-full | last:     ) -> dict\[str, object\]: ... | Python text file: difficulty_profile_port.py | 내부 |
| `./src/evalvault/ports/outbound/domain_memory_port.py` | Python | code-backend | lens:개발;type:소스 | 포함 | - | 2026-01-28T17:56:20 | read-full | last:     ... | Python text file: Domain Memory port interface for factual, experiential, and working memory layer | 내부 |
| `./src/evalvault/ports/outbound/embedding_port.py` | Python | code-backend | lens:개발;type:소스 | 포함 | - | 2026-01-28T17:56:20 | read-full | last:         ... | Python text file: Embedding port interface. | 내부 |
| `./src/evalvault/ports/outbound/graph_retriever_port.py` | Python | code-backend | lens:개발;type:소스 | 포함 | - | 2026-01-28T17:56:20 | read-full | last:         """서브그래프를 LLM 컨텍스트로 변환""" | Python text file: graph_retriever_port.py | 내부 |
| `./src/evalvault/ports/outbound/improvement_port.py` | Python | code-backend | lens:개발;type:소스 | 포함 | - | 2026-01-28T17:56:20 | read-full | last:         ... | Python text file: Ports for improvement analysis components. | 내부 |
| `./src/evalvault/ports/outbound/intent_classifier_port.py` | Python | code-backend | lens:개발;type:소스 | 포함 | - | 2026-01-28T17:56:20 | read-full | last:         ... | Python text file: Phase 14: Intent Classifier Port (Outbound). | 내부 |
| `./src/evalvault/ports/outbound/judge_calibration_port.py` | Python | code-backend | lens:개발;type:소스 | 포함 | - | 2026-01-28T17:56:20 | read-full | last:     ) -> JudgeCalibrationResult: ... | Python text file: judge_calibration_port.py | 내부 |
| `./src/evalvault/ports/outbound/korean_nlp_port.py` | Python | code-backend | lens:개발;type:소스 | 포함 | - | 2026-01-28T17:56:20 | read-full | last:         """Create and index a retriever for the documents.""" | Python text file: Ports for Korean NLP tooling used in benchmarks. | 내부 |
| `./src/evalvault/ports/outbound/llm_factory_port.py` | Python | code-backend | lens:개발;type:소스 | 포함 | - | 2026-01-28T17:56:20 | read-full | last:     ) -> LLMPort \| None: ... | Python text file: llm_factory_port.py | 내부 |
| `./src/evalvault/ports/outbound/llm_port.py` | Python | code-backend | lens:개발;type:소스 | 포함 | - | 2026-01-28T17:56:20 | read-full | last:         raise NotImplementedError("generate_text not implemented") | Python text file: LLM adapter port for Ragas evaluation. | 내부 |
| `./src/evalvault/ports/outbound/method_port.py` | Python | code-backend | lens:개발;type:소스 | 포함 | - | 2026-01-28T17:56:20 | read-full | last:         raise NotImplementedError | Python text file: Port for RAG method plugins. | 내부 |
| `./src/evalvault/ports/outbound/nlp_analysis_port.py` | Python | code-backend | lens:개발;type:소스 | 포함 | - | 2026-01-28T17:56:20 | read-full | last:         ... | Python text file: NLP 분석 서비스 인터페이스. | 내부 |
| `./src/evalvault/ports/outbound/ops_snapshot_port.py` | Python | code-backend | lens:개발;type:소스 | 포함 | - | 2026-01-28T17:56:20 | read-full | last:     def write_snapshot(self, path: Path, payload: dict\[str, Any\]) -> None: ... | Python text file: ops_snapshot_port.py | 내부 |
| `./src/evalvault/ports/outbound/relation_augmenter_port.py` | Python | code-backend | lens:개발;type:소스 | 포함 | - | 2026-01-28T17:56:20 | read-full | last:         raise NotImplementedError | Python text file: Port for augmenting low-confidence relations via external services. | 내부 |
| `./src/evalvault/ports/outbound/report_port.py` | Python | code-backend | lens:개발;type:소스 | 포함 | - | 2026-01-28T17:56:20 | read-full | last:         ... | Python text file: Report generation port interface. | 내부 |
| `./src/evalvault/ports/outbound/stage_storage_port.py` | Python | code-backend | lens:개발;type:소스 | 포함 | - | 2026-01-28T17:56:20 | read-full | last:         ... | Python text file: Stage event/metric storage port. | 내부 |
| `./src/evalvault/ports/outbound/storage_port.py` | Python | code-backend | lens:개발;type:소스 | 포함 | - | 2026-01-28T17:56:20 | read-full | last:         ... | Python text file: 결과 저장 인터페이스. | 내부 |
| `./src/evalvault/ports/outbound/tracer_port.py` | Python | code-backend | lens:개발;type:소스 | 포함 | - | 2026-01-28T17:56:20 | read-full | last:         ... | Python text file: Outbound port for tracing spans without infrastructure coupling. | 내부 |
| `./src/evalvault/ports/outbound/tracker_port.py` | Python | code-backend | lens:개발;type:소스 | 포함 | - | 2026-01-28T17:56:20 | read-full | last:         ... | Python text file: Tracker port interface for logging evaluation traces. | 내부 |
| `./src/evalvault/reports/__init__.py` | Python | code-backend | lens:개발;type:소스 | 포함 | - | 2026-01-28T17:56:20 | read-full | last: __all__ = \["build_release_notes"\] | Python text file: Release/report helpers. | 내부 |
| `./src/evalvault/reports/release_notes.py` | Python | code-backend | lens:개발;type:소스 | 포함 | - | 2026-01-28T17:56:20 | read-full | last:     return "\n".join(\[line.rstrip() for line in lines if line is not None\]).strip() + "\n" | Python text file: Utility helpers for building EvalVault release notes. | 내부 |
| `./src/evalvault/scripts/__init__.py` | Python | code-backend | lens:개발;type:소스 | 포함 | - | 2026-01-28T17:56:20 | read-full | last: __all__ = \["regression_runner"\] | Python text file: Utility helpers for standalone EvalVault scripts. | 내부 |
| `./src/evalvault/scripts/regression_runner.py` | Python | code-backend | lens:개발;type:소스 | 포함 | - | 2026-01-28T17:56:20 | read-full | last: \] | Python text file: Regression runner utilities used by automation scripts. | 내부 |
| `./tests/__init__.py` | Python | tests | lens:QA;type:테스트 | 포함 | - | 2026-01-28T17:56:20 | read-full | last: (empty) | Python text file: __init__.py | 내부 |
| `./tests/conftest.py` | Python | tests | lens:QA;type:테스트 | 포함 | - | 2026-01-28T17:56:20 | read-full | last:         config.option.dist = "loadscope" | Python text file: Shared pytest configuration for optional parallel runs. | 내부 |
| `./tests/fixtures/README.md` | Markdown | tests | lens:QA;type:테스트 | 포함 | - | 2026-01-28T17:56:20 | read-full | last: - CSV/Excel 파일은 JSON과 동일한 데이터를 다른 형식으로 제공합니다 | Markdown text file: Test Fixtures | 내부 |
| `./tests/fixtures/benchmark/retrieval_ground_truth_min.json` | JSON | tests | lens:QA;type:테스트 | 포함 | - | 2026-01-28T17:56:20 | read-full | keys: name,version,description,documents,test_cases; last: } | JSON object with 5 keys | 내부 |
| `./tests/fixtures/benchmark/retrieval_ground_truth_multi.json` | JSON | tests | lens:QA;type:테스트 | 포함 | - | 2026-01-28T17:56:20 | read-full | keys: name,version,description,documents,test_cases; last: } | JSON object with 5 keys | 내부 |
| `./tests/fixtures/e2e/auto_insurance_qa_korean_full.json` | JSON | tests | lens:QA;type:테스트 | 포함 | - | 2026-01-28T17:56:20 | read-full | keys: name,version,description,thresholds,test_cases; last: } | JSON object with 5 keys | 내부 |
| `./tests/fixtures/e2e/callcenter_summary_5cases.json` | JSON | tests | lens:QA;type:테스트 | 포함 | - | 2026-01-28T17:56:20 | read-full | keys: name,version,description,thresholds,test_cases; last: } | JSON object with 5 keys | 내부 |
| `./tests/fixtures/e2e/comprehensive_dataset.json` | JSON | tests | lens:QA;type:테스트 | 포함 | - | 2026-01-28T17:56:20 | read-full | keys: name,version,metadata,thresholds,test_cases; last: } | JSON object with 5 keys | 내부 |
| `./tests/fixtures/e2e/edge_cases.json` | JSON | tests | lens:QA;type:테스트 | 포함 | - | 2026-01-28T17:56:20 | read-full | keys: name,version,description,test_cases; last: } | JSON object with 4 keys | 내부 |
| `./tests/fixtures/e2e/edge_cases.xlsx` | XLSX | tests | lens:QA;type:테스트 | 포함 | - | 2026-01-28T17:56:20 | read-full | sheets: 1; Sheet1:8r | XLSX sheets=1 | 내부 |
| `./tests/fixtures/e2e/evaluation_test_sample.json` | JSON | tests | lens:QA;type:테스트 | 포함 | - | 2026-01-28T17:56:20 | read-full | keys: name,version,description,test_cases; last: } | JSON object with 4 keys | 내부 |
| `./tests/fixtures/e2e/graphrag_benchmark.json` | JSON | tests | lens:QA;type:테스트 | 포함 | - | 2026-01-28T17:56:20 | read-full | keys: name,version,description,thresholds,test_cases; last: } | JSON object with 5 keys | 내부 |
| `./tests/fixtures/e2e/graphrag_multi_sample.json` | JSON | tests | lens:QA;type:테스트 | 포함 | - | 2026-01-28T17:56:20 | read-full | keys: name,version,description,thresholds,test_cases; last: } | JSON object with 5 keys | 내부 |
| `./tests/fixtures/e2e/graphrag_retriever_docs.json` | JSON | tests | lens:QA;type:테스트 | 포함 | - | 2026-01-28T17:56:20 | read-full | keys: documents; last: } | JSON object with 1 keys | 내부 |
| `./tests/fixtures/e2e/graphrag_smoke.json` | JSON | tests | lens:QA;type:테스트 | 포함 | - | 2026-01-28T17:56:20 | read-full | keys: name,version,description,thresholds,test_cases; last: } | JSON object with 5 keys | 내부 |
| `./tests/fixtures/e2e/insurance_document.txt` | Text | tests | lens:QA;type:테스트 | 포함 | - | 2026-01-28T17:56:20 | read-full | last: 14일 이내 보상금 지급 (서류 완비 시) | Text text file: insurance_document.txt | 내부 |
| `./tests/fixtures/e2e/insurance_qa_english.csv` | CSV | tests | lens:QA;type:테스트 | 포함 | - | 2026-01-28T17:56:20 | read-full | lines: 6; last: en-005,What is the waiting period for illness coverage?,There is a 90-day waiting period for illness-related claims.,"\[" | CSV lines=6 | 내부 |
| `./tests/fixtures/e2e/insurance_qa_english.json` | JSON | tests | lens:QA;type:테스트 | 포함 | - | 2026-01-28T17:56:20 | read-full | keys: name,version,description,test_cases; last: } | JSON object with 4 keys | 내부 |
| `./tests/fixtures/e2e/insurance_qa_english.xlsx` | XLSX | tests | lens:QA;type:테스트 | 포함 | - | 2026-01-28T17:56:20 | read-full | sheets: 1; Sheet1:6r | XLSX sheets=1 | 내부 |
| `./tests/fixtures/e2e/insurance_qa_korean.csv` | CSV | tests | lens:QA;type:테스트 | 포함 | - | 2026-01-28T17:56:20 | read-full | lines: 6; last: kr-005,입원비 보장은 어떻게 되나요?,질병 입원 시 1일당 5만원의 입원비가 지급됩니다.,"\[""질병으로 인한 입원 시 1일당 5만원(최대 180일)이 지급됩니다."",""상해로 인한 입원은 별도의 상해입원비 | CSV lines=6 | 내부 |
| `./tests/fixtures/e2e/insurance_qa_korean.json` | JSON | tests | lens:QA;type:테스트 | 포함 | - | 2026-01-28T17:56:20 | read-full | keys: name,version,description,metadata,thresholds,test_cases; last: } | JSON object with 6 keys | 내부 |
| `./tests/fixtures/e2e/insurance_qa_korean.xlsx` | XLSX | tests | lens:QA;type:테스트 | 포함 | - | 2026-01-28T17:56:20 | read-full | sheets: 1; Sheet1:6r | XLSX sheets=1 | 내부 |
| `./tests/fixtures/e2e/insurance_qa_korean_versioned_pdf.json` | JSON | tests | lens:QA;type:테스트 | 포함 | - | 2026-01-28T17:56:20 | read-full | keys: name,version,description,metadata,thresholds,test_cases; last: } | JSON object with 6 keys | 내부 |
| `./tests/fixtures/e2e/multiturn_benchmark.json` | JSON | tests | lens:QA;type:테스트 | 포함 | - | 2026-01-28T17:56:20 | read-full | keys: name,version,test_cases; last: } | JSON object with 3 keys | 내부 |
| `./tests/fixtures/e2e/regression_baseline.json` | JSON | tests | lens:QA;type:테스트 | 포함 | - | 2026-01-28T17:56:20 | read-full | keys: name,version,description,metadata,thresholds,test_cases; last: } | JSON object with 6 keys | 내부 |
| `./tests/fixtures/e2e/run_mode_full_domain_memory.json` | JSON | tests | lens:QA;type:테스트 | 포함 | - | 2026-01-28T17:56:20 | read-full | keys: name,version,description,metadata,thresholds,test_cases; last: } | JSON object with 6 keys | 내부 |
| `./tests/fixtures/e2e/run_mode_simple.json` | JSON | tests | lens:QA;type:테스트 | 포함 | - | 2026-01-28T17:56:20 | read-full | keys: name,version,description,thresholds,test_cases; last: } | JSON object with 5 keys | 내부 |
| `./tests/fixtures/e2e/summary_eval_minimal.json` | JSON | tests | lens:QA;type:테스트 | 포함 | - | 2026-01-28T17:56:20 | read-full | keys: name,version,description,thresholds,test_cases; last: } | JSON object with 5 keys | 내부 |
| `./tests/fixtures/kg/minimal_graph.json` | JSON | tests | lens:QA;type:테스트 | 포함 | - | 2026-01-28T17:56:20 | read-full | keys: entities,relations; last: } | JSON object with 2 keys | 내부 |
| `./tests/fixtures/sample_dataset.csv` | CSV | tests | lens:QA;type:테스트 | 포함 | - | 2026-01-28T17:56:20 | read-full | lines: 5; last: test_004,What is TDD?,TDD means Test-Driven Development.,Test-Driven Development\|Write tests first\|Red-Green-Refactor cy | CSV lines=5 | 내부 |
| `./tests/fixtures/sample_dataset.json` | JSON | tests | lens:QA;type:테스트 | 포함 | - | 2026-01-28T17:56:20 | read-full | keys: name,version,thresholds,test_cases; last: } | JSON object with 4 keys | 내부 |
| `./tests/fixtures/sample_dataset.xlsx` | XLSX | tests | lens:QA;type:테스트 | 포함 | - | 2026-01-28T17:56:20 | read-full | sheets: 1; test_cases:5r | XLSX sheets=1 | 내부 |
| `./tests/integration/__init__.py` | Python | tests | lens:QA;type:테스트 | 포함 | - | 2026-01-28T17:56:20 | read-full | last: """Integration tests for EvalVault.""" | Python text file: Integration tests for EvalVault. | 내부 |
| `./tests/integration/benchmark/test_benchmark_service_integration.py` | Python | tests | lens:QA;type:테스트 | 포함 | - | 2026-01-28T17:56:20 | read-full | last:         assert score.metrics\["acc,none"\] == 0.75 | Python text file: Integration tests for BenchmarkService with storage and mocked benchmark adapter | 내부 |
| `./tests/integration/conftest.py` | Python | tests | lens:QA;type:테스트 | 포함 | - | 2026-01-28T17:56:20 | read-full | last:             pytest.skip("Requires OpenTelemetry dependencies (uv sync --extra phoenix)") | Python text file: Integration test fixtures and configuration. | 내부 |
| `./tests/integration/test_cli_integration.py` | Python | tests | lens:QA;type:테스트 | 포함 | - | 2026-01-28T17:56:20 | read-full | last:             apply_profile(settings, "nonexistent_profile_12345") | Python text file: CLI integration tests for --profile option. | 내부 |
| `./tests/integration/test_data_flow.py` | Python | tests | lens:QA;type:테스트 | 포함 | - | 2026-01-28T17:56:20 | read-full | last:         assert ragas_dict\["retrieved_contexts"\] == \["Context"\] | Python text file: Integration tests for data loading flow. | 내부 |
| `./tests/integration/test_e2e_scenarios.py` | Python | tests | lens:QA;type:테스트 | 포함 | - | 2026-01-28T17:56:20 | read-full | last:         assert elapsed < timeout | Python text file: End-to-End test scenarios for EvalVault. | 내부 |
| `./tests/integration/test_evaluation_flow.py` | Python | tests | lens:QA;type:테스트 | 포함 | - | 2026-01-28T17:56:20 | read-full | last:         assert exact_score.passed is True  # >= threshold | Python text file: Integration tests for evaluation flow. | 내부 |
| `./tests/integration/test_full_workflow.py` | Python | tests | lens:QA;type:테스트 | 포함 | - | 2026-01-28T17:56:20 | read-full | last:         print("\n  ✓ ThinkingConfig interface works correctly") | Python text file: Full Workflow Integration Tests with Real API. | 내부 |
| `./tests/integration/test_langfuse_flow.py` | Python | tests | lens:QA;type:테스트 | 포함 | - | 2026-01-28T17:56:20 | read-full | last:         assert callable(adapter.log_evaluation_run) | Python text file: Integration tests for Langfuse tracking flow. | 내부 |
| `./tests/integration/test_phoenix_flow.py` | Python | tests | lens:QA;type:테스트 | 포함 | - | 2026-01-28T17:56:20 | read-full | last:         assert hasattr(tracker, "MLflowAdapter") | Python text file: Integration tests for Phoenix tracking flow. | 내부 |
| `./tests/integration/test_pipeline_api_contracts.py` | Python | tests | lens:QA;type:테스트 | 포함 | - | 2026-01-28T17:56:20 | read-full | last:     assert response.headers.get("Retry-After") | Python text file: Pipeline API contract tests for Web UI compatibility. | 내부 |
| `./tests/integration/test_storage_flow.py` | Python | tests | lens:QA;type:테스트 | 포함 | - | 2026-01-28T17:56:20 | read-full | last:             assert retrieved.run_id == run.run_id | Python text file: Integration tests for storage flow with RagasEvaluator. | 내부 |
| `./tests/integration/test_summary_eval_fixture.py` | Python | tests | lens:QA;type:테스트 | 포함 | - | 2026-01-28T17:56:20 | read-full | last:         assert 2 <= len(test_case.contexts) <= 3 | Python text file: Integration test for the summary evaluation minimal fixture. | 내부 |
| `./tests/optional_deps.py` | Python | tests | lens:QA;type:테스트 | 포함 | - | 2026-01-28T17:56:20 | read-full | last:     return _SKLEARN_STATE | Python text file: optional_deps.py | 내부 |
| `./tests/unit/__init__.py` | Python | tests | lens:QA;type:테스트 | 포함 | - | 2026-01-28T17:56:20 | read-full | last: (empty) | Python text file: __init__.py | 내부 |
| `./tests/unit/adapters/inbound/mcp/test_execute_tools.py` | Python | tests | lens:QA;type:테스트 | 포함 | - | 2026-01-28T17:56:20 | read-full | last:     assert Path(response.artifacts.json_path).exists() | Python text file: test_execute_tools.py | 내부 |
| `./tests/unit/adapters/inbound/mcp/test_read_tools.py` | Python | tests | lens:QA;type:테스트 | 포함 | - | 2026-01-28T17:56:20 | read-full | last:     assert response.artifacts.artifacts_index_path == str(index_path) | Python text file: test_read_tools.py | 내부 |
| `./tests/unit/adapters/outbound/documents/test_pdf_extractor.py` | Python | tests | lens:QA;type:테스트 | 포함 | - | 2026-01-28T17:56:20 | read-full | last:         pdf_extractor.extract_text_from_pdf(pdf, enable_ocr=True, ocr_backend="unknown") | Python text file: test_pdf_extractor.py | 내부 |
| `./tests/unit/adapters/outbound/documents/test_versioned_loader.py` | Python | tests | lens:QA;type:테스트 | 포함 | - | 2026-01-28T17:56:20 | read-full | last:         load_versioned_chunks_from_pdf_dir(tmp_path) | Python text file: test_versioned_loader.py | 내부 |
| `./tests/unit/adapters/outbound/improvement/__init__.py` | Python | tests | lens:QA;type:테스트 | 포함 | - | 2026-01-28T17:56:20 | read-full | last: """Unit tests for improvement adapters.""" | Python text file: Unit tests for improvement adapters. | 내부 |
| `./tests/unit/adapters/outbound/improvement/test_insight_generator.py` | Python | tests | lens:QA;type:테스트 | 포함 | - | 2026-01-28T17:56:20 | read-full | last:         assert len(insight.prioritized_improvements) == 1 | Python text file: Unit tests for InsightGenerator. | 내부 |
| `./tests/unit/adapters/outbound/improvement/test_pattern_detector.py` | Python | tests | lens:QA;type:테스트 | 포함 | - | 2026-01-28T17:56:20 | read-full | last:             assert result\["correlation"\] < 0 | Python text file: Unit tests for PatternDetector. | 내부 |
| `./tests/unit/adapters/outbound/improvement/test_playbook_loader.py` | Python | tests | lens:QA;type:테스트 | 포함 | - | 2026-01-28T17:56:20 | read-full | last:         assert "entity_preservation" in playbook.metrics | Python text file: Unit tests for PlaybookLoader. | 내부 |
| `./tests/unit/adapters/outbound/improvement/test_stage_metric_playbook_loader.py` | Python | tests | lens:QA;type:테스트 | 포함 | - | 2026-01-28T17:56:20 | read-full | last:     assert playbook == {} | Python text file: Unit tests for StageMetricPlaybookLoader. | 내부 |
| `./tests/unit/adapters/outbound/kg/test_graph_rag_retriever.py` | Python | tests | lens:QA;type:테스트 | 포함 | - | 2026-01-28T17:56:20 | read-full | last:     assert results\[0\].doc_id == "doc-003" | Python text file: Unit tests for GraphRAGRetriever. | 내부 |
| `./tests/unit/adapters/outbound/kg/test_parallel_kg_builder.py` | Python | tests | lens:QA;type:테스트 | 포함 | - | 2026-01-28T17:56:20 | read-full | last:     assert result.documents_by_id == {} | Python text file: Tests for ParallelKGBuilder. | 내부 |
| `./tests/unit/adapters/outbound/retriever/test_graph_rag_adapter.py` | Python | tests | lens:QA;type:테스트 | 포함 | - | 2026-01-28T17:56:20 | read-full | last:     assert "BetaPlan" in context | Python text file: Unit tests for GraphRAGAdapter. | 내부 |
| `./tests/unit/adapters/outbound/storage/test_benchmark_storage_adapter.py` | Python | tests | lens:QA;type:테스트 | 포함 | - | 2026-01-28T17:56:20 | read-full | last:         assert ts.version == "2" | Python text file: Unit tests for SQLiteBenchmarkStorageAdapter. | 내부 |
| `./tests/unit/config/test_phoenix_support.py` | Python | tests | lens:QA;type:테스트 | 포함 | - | 2026-01-28T17:56:20 | read-full | last:     assert len(dummy_service.calls) == 1 | Python text file: Tests for phoenix_support helper utilities. | 내부 |
| `./tests/unit/conftest.py` | Python | tests | lens:QA;type:테스트 | 포함 | - | 2026-01-28T17:56:20 | read-full | last:     return os.environ.get("OPENAI_MODEL", "gpt-5-mini") | Python text file: conftest.py | 내부 |
| `./tests/unit/domain/metrics/test_analysis_metric_registry.py` | Python | tests | lens:QA;type:테스트 | 포함 | - | 2026-01-28T17:56:20 | read-full | last:         assert spec.description | Python text file: Tests for analysis metric registry. | 내부 |
| `./tests/unit/domain/metrics/test_confidence.py` | Python | tests | lens:QA;type:테스트 | 포함 | - | 2026-01-28T17:56:20 | read-full | last:             assert isinstance(result, bool) | Python text file: Tests for Confidence Score metric. | 내부 |
| `./tests/unit/domain/metrics/test_contextual_relevancy.py` | Python | tests | lens:QA;type:테스트 | 포함 | - | 2026-01-28T17:56:20 | read-full | last:         assert 0.0 <= score <= 1.0 | Python text file: Tests for Contextual Relevancy metric. | 내부 |
| `./tests/unit/domain/metrics/test_entity_preservation.py` | Python | tests | lens:QA;type:테스트 | 포함 | - | 2026-01-28T17:56:20 | read-full | last:     assert score == pytest.approx(0.0) | Python text file: test_entity_preservation.py | 내부 |
| `./tests/unit/domain/metrics/test_metric_registry.py` | Python | tests | lens:QA;type:테스트 | 포함 | - | 2026-01-28T17:56:20 | read-full | last:         assert spec.signal_group | Python text file: Tests for metric registry. | 내부 |
| `./tests/unit/domain/metrics/test_multiturn_metrics.py` | Python | tests | lens:QA;type:테스트 | 포함 | - | 2026-01-28T17:56:20 | read-full | last:     assert calculate_turn_latency_p95(\[None, 100, None, 200, 300\]) == 290.0 | Python text file: test_multiturn_metrics.py | 내부 |
| `./tests/unit/domain/metrics/test_no_answer.py` | Python | tests | lens:QA;type:테스트 | 포함 | - | 2026-01-28T17:56:20 | read-full | last:         assert score == 1.0 | Python text file: Tests for NoAnswerAccuracy metric. | 내부 |
| `./tests/unit/domain/metrics/test_retrieval_rank.py` | Python | tests | lens:QA;type:테스트 | 포함 | - | 2026-01-28T17:56:20 | read-full | last:         assert mrr_detailed\["num_relevant"\] == 2 | Python text file: Tests for retrieval ranking metrics (MRR, NDCG, HitRate). | 내부 |
| `./tests/unit/domain/metrics/test_text_match.py` | Python | tests | lens:QA;type:테스트 | 포함 | - | 2026-01-28T17:56:20 | read-full | last:         assert 0.1 < score < 1.0 | Python text file: Tests for ExactMatch and F1Score metrics. | 내부 |
| `./tests/unit/domain/services/test_cache_metrics.py` | Python | tests | lens:QA;type:테스트 | 포함 | - | 2026-01-28T17:56:20 | read-full | last:     assert window_no_update.hits == 2 | Python text file: Cache metrics helpers tests. | 내부 |
| `./tests/unit/domain/services/test_claim_level.py` | Python | tests | lens:QA;type:테스트 | 포함 | - | 2026-01-28T17:56:20 | read-full | last:         assert result is None | Python text file: Tests for claim-level faithfulness functionality. | 내부 |
| `./tests/unit/domain/services/test_dataset_preprocessor.py` | Python | tests | lens:QA;type:테스트 | 포함 | - | 2026-01-28T17:56:20 | read-full | last:     assert report.references_missing == 1 | Python text file: test_dataset_preprocessor.py | 내부 |
| `./tests/unit/domain/services/test_document_versioning.py` | Python | tests | lens:QA;type:테스트 | 포함 | - | 2026-01-28T17:56:20 | read-full | last:     assert sorted(\[c.doc_id for c in selected\]) == \["A:2024-04-01#1", "B:2023-01-01#1"\] | Python text file: test_document_versioning.py | 내부 |
| `./tests/unit/domain/services/test_evaluator_comprehensive.py` | Python | tests | lens:QA;type:테스트 | 포함 | - | 2026-01-28T17:56:20 | read-full | last:         assert result.tracker_metadata\["dataset_preprocess"\] == {"findings": \["test finding"\]} | Python text file: Comprehensive tests for RagasEvaluator service. | 내부 |
| `./tests/unit/domain/services/test_holdout_splitter.py` | Python | tests | lens:QA;type:테스트 | 포함 | - | 2026-01-28T17:56:20 | read-full | last:     assert len(dev.test_cases) == 5 | Python text file: test_holdout_splitter.py | 내부 |
| `./tests/unit/domain/services/test_improvement_guide_service.py` | Python | tests | lens:QA;type:테스트 | 포함 | - | 2026-01-28T17:56:20 | read-full | last:         assert len(critical) == 2 | Python text file: Unit tests for ImprovementGuideService. | 내부 |
| `./tests/unit/domain/services/test_judge_calibration_service.py` | Python | tests | lens:QA;type:테스트 | 포함 | - | 2026-01-28T17:56:20 | read-full | last:     assert result.metrics\[0\].warning | Python text file: test_judge_calibration_service.py | 내부 |
| `./tests/unit/domain/services/test_ops_snapshot_service.py` | Python | tests | lens:QA;type:테스트 | 포함 | - | 2026-01-28T17:56:20 | read-full | last:     assert payload\["data"\]\["env"\]\["openai_api_key"\] == "\[redacted\]" | Python text file: test_ops_snapshot_service.py | 내부 |
| `./tests/unit/domain/services/test_regression_gate_service.py` | Python | tests | lens:QA;type:테스트 | 포함 | - | 2026-01-28T17:56:20 | read-full | last:         service.run_gate("candidate", "baseline") | Python text file: Regression gate service tests. | 내부 |
| `./tests/unit/domain/services/test_retrieval_metrics.py` | Python | tests | lens:QA;type:테스트 | 포함 | - | 2026-01-28T17:56:20 | read-full | last:     assert metrics\["ndcg_at_5"\] == 0.0 | Python text file: Retrieval metric utility tests. | 내부 |
| `./tests/unit/domain/services/test_retriever_context.py` | Python | tests | lens:QA;type:테스트 | 포함 | - | 2026-01-28T17:56:20 | read-full | last:     assert _extract_graph_attributes(results) == {} | Python text file: Retriever context helpers tests. | 내부 |
| `./tests/unit/domain/services/test_stage_event_builder.py` | Python | tests | lens:QA;type:테스트 | 포함 | - | 2026-01-28T17:56:20 | read-full | last:     assert retrieval_event.attributes\["community_id"\] == "c-1" | Python text file: Unit tests for StageEventBuilder. | 내부 |
| `./tests/unit/domain/services/test_stage_metric_guide_service.py` | Python | tests | lens:QA;type:테스트 | 포함 | - | 2026-01-28T17:56:20 | read-full | last:     assert action.effort == EffortLevel.HIGH | Python text file: Unit tests for StageMetricGuideService. | 내부 |
| `./tests/unit/domain/services/test_synthetic_qa_generator.py` | Python | tests | lens:QA;type:테스트 | 포함 | - | 2026-01-28T17:56:20 | read-full | last:         assert "answer" in prompt.lower() | Python text file: Tests for SyntheticQAGenerator. | 내부 |
| `./tests/unit/domain/test_embedding_overlay.py` | Python | tests | lens:QA;type:테스트 | 포함 | - | 2026-01-28T17:56:20 | read-full | last:     assert facts == \[\] | Python text file: Tests for embedding overlay helpers. | 내부 |
| `./tests/unit/domain/test_prompt_manifest.py` | Python | tests | lens:QA;type:테스트 | 포함 | - | 2026-01-28T17:56:20 | read-full | last:     assert summaries\[1\].status == "missing_file" | Python text file: Tests for prompt manifest helpers. | 내부 |
| `./tests/unit/domain/test_prompt_status.py` | Python | tests | lens:QA;type:테스트 | 포함 | - | 2026-01-28T17:56:20 | read-full | last:     assert format_prompt_section(\[\], style="markdown") == "" | Python text file: Tests for prompt status formatting helpers. | 내부 |
| `./tests/unit/reports/test_release_notes.py` | Python | tests | lens:QA;type:테스트 | 포함 | - | 2026-01-28T17:56:20 | read-full | last:     assert "system.txt" in markdown | Python text file: Tests for release notes builder. | 내부 |
| `./tests/unit/scripts/test_regression_runner.py` | Python | tests | lens:QA;type:테스트 | 포함 | - | 2026-01-28T17:56:20 | read-full | last:     assert "pass-suite" in summary | Python text file: Tests for the regression runner utilities. | 내부 |
| `./tests/unit/test_agent_types.py` | Python | tests | lens:QA;type:테스트 | 포함 | - | 2026-01-28T17:56:20 | read-full | last:         assert "docs/IMPROVEMENT_PLAN.md" in critical | Python text file: Unit tests for agent types configuration. | 내부 |
| `./tests/unit/test_analysis_entities.py` | Python | tests | lens:QA;type:테스트 | 포함 | - | 2026-01-28T17:56:20 | read-full | last:         assert EffectSizeLevel.LARGE.value == "large" | Python text file: Tests for analysis domain entities. | 내부 |
| `./tests/unit/test_analysis_modules.py` | Python | tests | lens:QA;type:테스트 | 포함 | - | 2026-01-28T17:56:20 | read-full | last:         assert result\["comparisons"\]\[0\]\["direction"\] == "up" | Python text file: Phase 14.4: Analysis Module Adapters 단위 테스트. | 내부 |
| `./tests/unit/test_analysis_pipeline.py` | Python | tests | lens:QA;type:테스트 | 포함 | - | 2026-01-28T17:56:20 | read-full | last:         assert "data_loader" in deps | Python text file: Phase 14.1: Analysis Pipeline 엔티티 단위 테스트. | 내부 |
| `./tests/unit/test_analysis_service.py` | Python | tests | lens:QA;type:테스트 | 포함 | - | 2026-01-28T17:56:20 | read-full | last:         assert "High vocabulary diversity" in result.nlp.insights | Python text file: Tests for Analysis Service. | 내부 |
| `./tests/unit/test_anthropic_adapter.py` | Python | tests | lens:QA;type:테스트 | 포함 | - | 2026-01-28T17:56:20 | read-full | last:         assert adapter.get_thinking_budget() == 10000 | Python text file: Tests for Anthropic Claude LLM adapter. | 내부 |
| `./tests/unit/test_artifact_lint_service.py` | Python | tests | lens:QA;type:테스트 | 포함 | - | 2026-01-28T17:56:20 | read-full | last:     assert any(issue.code == "artifacts.index.node.path.missing" for issue in summary.issues) | Python text file: test_artifact_lint_service.py | 내부 |
| `./tests/unit/test_async_batch_executor.py` | Python | tests | lens:QA;type:테스트 | 포함 | - | 2026-01-28T17:56:20 | read-full | last:         assert executor.get_current_batch_size() < 10 | Python text file: Tests for Async Batch Executor. | 내부 |
| `./tests/unit/test_azure_adapter.py` | Python | tests | lens:QA;type:테스트 | 포함 | - | 2026-01-28T17:56:20 | read-full | last:         ) | Python text file: Tests for Azure OpenAI LLM adapter. | 내부 |
| `./tests/unit/test_benchmark_helpers.py` | Python | tests | lens:QA;type:테스트 | 포함 | - | 2026-01-28T17:56:20 | read-full | last:     assert loaded\["overall"\]\["best"\] == "bm25" | Python text file: Benchmark CLI helper utilities tests. | 내부 |
| `./tests/unit/test_benchmark_runner.py` | Python | tests | lens:QA;type:테스트 | 포함 | - | 2026-01-28T17:56:20 | read-full | last:             assert "average" in leaderboard | Python text file: Korean RAG Benchmark Runner 테스트. | 내부 |
| `./tests/unit/test_causal_adapter.py` | Python | tests | lens:QA;type:테스트 | 포함 | - | 2026-01-28T17:56:20 | read-full | last:                 break | Python text file: Tests for CausalAnalysisAdapter. | 내부 |
| `./tests/unit/test_ci_gate_cli.py` | Python | tests | lens:QA;type:테스트 | 포함 | - | 2026-01-28T17:56:20 | read-full | last:     assert payload\["regression_rate"\] == 0.5 | Python text file: CLI tests for ci-gate command. | 내부 |
| `./tests/unit/test_cli.py` | Python | tests | lens:QA;type:테스트 | 포함 | - | 2026-01-28T17:56:20 | read-full | last:         assert not run_command_module._is_oss_open_model(None) | Python text file: Tests for CLI interface. | 내부 |
| `./tests/unit/test_cli_artifacts.py` | Python | tests | lens:QA;type:테스트 | 포함 | - | 2026-01-28T17:56:20 | read-full | last:     assert "artifacts.lint" in output_path.read_text(encoding="utf-8") | Python text file: test_cli_artifacts.py | 내부 |
| `./tests/unit/test_cli_calibrate_judge.py` | Python | tests | lens:QA;type:테스트 | 포함 | - | 2026-01-28T17:56:20 | read-full | last:     storage.update_run_metadata.assert_not_called() | Python text file: test_cli_calibrate_judge.py | 내부 |
| `./tests/unit/test_cli_domain.py` | Python | tests | lens:QA;type:테스트 | 포함 | - | 2026-01-28T17:56:20 | read-full | last:         assert "completed" in result.stdout.lower() | Python text file: Tests for domain memory CLI commands. | 내부 |
| `./tests/unit/test_cli_init.py` | Python | tests | lens:QA;type:테스트 | 포함 | - | 2026-01-28T17:56:20 | read-full | last:         assert "help" in result.stdout.lower() or "usage" in result.stdout.lower() | Python text file: Tests for init CLI command. | 내부 |
| `./tests/unit/test_cli_ops.py` | Python | tests | lens:QA;type:테스트 | 포함 | - | 2026-01-28T17:56:20 | read-full | last:     assert "--output" in stdout | Python text file: test_cli_ops.py | 내부 |
| `./tests/unit/test_cli_progress.py` | Python | tests | lens:QA;type:테스트 | 포함 | - | 2026-01-28T17:56:20 | read-full | last:         assert multi_stage_progress is not None | Python text file: Unit tests for CLI progress utilities. | 내부 |
| `./tests/unit/test_cli_utils.py` | Python | tests | lens:QA;type:테스트 | 포함 | - | 2026-01-28T17:56:20 | read-full | last:     assert f"Path: {expected_path}" in "\n".join(fixes) | Python text file: test_cli_utils.py | 내부 |
| `./tests/unit/test_data_loaders.py` | Python | tests | lens:QA;type:테스트 | 포함 | - | 2026-01-28T17:56:20 | read-full | last:         assert item\["reference"\] == "Python is a high-level interpreted programming language." | Python text file: Tests for dataset loaders. | 내부 |
| `./tests/unit/test_difficulty_profiling_service.py` | Python | tests | lens:QA;type:테스트 | 포함 | - | 2026-01-28T17:56:20 | read-full | last:     writer_adapter.write_profile.assert_not_called() | Python text file: test_difficulty_profiling_service.py | 내부 |
| `./tests/unit/test_domain_config.py` | Python | tests | lens:QA;type:테스트 | 포함 | - | 2026-01-28T17:56:20 | read-full | last:             Path(temp_path).unlink() | Python text file: Unit tests for domain configuration module. | 내부 |
| `./tests/unit/test_domain_memory.py` | Python | tests | lens:QA;type:테스트 | 포함 | - | 2026-01-28T17:56:20 | read-full | last:         assert kg_fact.is_linked_to_kg() is True | Python text file: Unit tests for Domain Memory entities and SQLite adapter. | 내부 |
| `./tests/unit/test_entities.py` | Python | tests | lens:QA;type:테스트 | 포함 | - | 2026-01-28T17:56:20 | read-full | last:         assert summary\["avg_faithfulness"\] == 0.9 | Python text file: Tests for domain entities. | 내부 |
| `./tests/unit/test_entities_kg.py` | Python | tests | lens:QA;type:테스트 | 포함 | - | 2026-01-28T17:56:20 | read-full | last:     assert attrs\["attributes"\]\["note"\].startswith("부모") | Python text file: Unit tests for knowledge graph entity and relation models. | 내부 |
| `./tests/unit/test_entity_extractor.py` | Python | tests | lens:QA;type:테스트 | 포함 | - | 2026-01-28T17:56:20 | read-full | last:         assert len(samsung_entities) <= 3 | Python text file: Unit tests for entity extractor. | 내부 |
| `./tests/unit/test_evaluator.py` | Python | tests | lens:QA;type:테스트 | 포함 | - | 2026-01-28T17:56:20 | read-full | last:             assert parallel_time < 0.5  # Should be much faster than 100ms | Python text file: Tests for Ragas evaluator service. | 내부 |
| `./tests/unit/test_experiment.py` | Python | tests | lens:QA;type:테스트 | 포함 | - | 2026-01-28T17:56:20 | read-full | last:         assert completed_exps\[0\].name == "Completed Experiment" | Python text file: Tests for Experiment entity and ExperimentManager service. | 내부 |
| `./tests/unit/test_hybrid_cache.py` | Python | tests | lens:QA;type:테스트 | 포함 | - | 2026-01-28T17:56:20 | read-full | last:         assert entry.access_count == 0 | Python text file: Tests for Hybrid Cache Adapter. | 내부 |
| `./tests/unit/test_instrumentation.py` | Python | tests | lens:QA;type:테스트 | 포함 | - | 2026-01-28T17:56:20 | read-full | last:             assert result is mock_tracer_provider | Python text file: Unit tests for Phoenix instrumentation configuration. | 내부 |
| `./tests/unit/test_insurance_metric.py` | Python | tests | lens:QA;type:테스트 | 포함 | - | 2026-01-28T17:56:20 | read-full | last:         assert metric.name == "insurance_term_accuracy" | Python text file: Unit tests for InsuranceTermAccuracy metric. | 내부 |
| `./tests/unit/test_intent_classifier.py` | Python | tests | lens:QA;type:테스트 | 포함 | - | 2026-01-28T17:56:20 | read-full | last:                     assert dep_id in node_ids, f"Invalid dependency {dep_id} in {intent} template" | Python text file: Phase 14.2: Intent Classifier 단위 테스트. | 내부 |
| `./tests/unit/test_kg_generator.py` | Python | tests | lens:QA;type:테스트 | 포함 | - | 2026-01-28T17:56:20 | read-full | last:         assert any(relation.provenance == "llm" for relation in relations) | Python text file: Unit tests for knowledge graph testset generator. | 내부 |
| `./tests/unit/test_kg_networkx.py` | Python | tests | lens:QA;type:테스트 | 포함 | - | 2026-01-28T17:56:20 | read-full | last:         assert query.metadata is None | Python text file: Unit tests for NetworkX Knowledge Graph adapter and query strategies. | 내부 |
| `./tests/unit/test_kiwi_tokenizer.py` | Python | tests | lens:QA;type:테스트 | 포함 | - | 2026-01-28T17:56:20 | read-full | last:         assert any(term in keyword_text for term in \["보험금", "피보험자", "사망", "보험", "지급"\]) | Python text file: KiwiTokenizer 단위 테스트. | 내부 |
| `./tests/unit/test_kiwi_warning_suppression.py` | Python | tests | lens:QA;type:테스트 | 포함 | - | 2026-01-28T17:56:20 | read-full | last:     assert tokenizer._model_type == "cong" | Python text file: Kiwi warning suppression helpers tests. | 내부 |
| `./tests/unit/test_korean_dense.py` | Python | tests | lens:QA;type:테스트 | 포함 | - | 2026-01-28T17:56:20 | read-full | last:         assert retriever._ollama_adapter is None | Python text file: Korean Dense Retriever unit tests. | 내부 |
| `./tests/unit/test_korean_evaluation.py` | Python | tests | lens:QA;type:테스트 | 포함 | - | 2026-01-28T17:56:20 | read-full | last:         assert result1_3.similarity > 0.3 | Python text file: Korean RAG Evaluation unit tests. | 내부 |
| `./tests/unit/test_korean_retrieval.py` | Python | tests | lens:QA;type:테스트 | 포함 | - | 2026-01-28T17:56:20 | read-full | last:         assert "자동차" not in results\[0\].document | Python text file: Korean Retrieval 단위 테스트. | 내부 |
| `./tests/unit/test_langfuse_tracker.py` | Python | tests | lens:QA;type:테스트 | 포함 | - | 2026-01-28T17:56:20 | read-full | last:         assert mock_span.start_span.call_count == 0 | Python text file: Tests for Langfuse tracker adapter. | 내부 |
| `./tests/unit/test_llm_relation_augmenter.py` | Python | tests | lens:QA;type:테스트 | 포함 | - | 2026-01-28T17:56:20 | read-full | last:     assert result == \[\] | Python text file: Tests for LLMRelationAugmenter. | 내부 |
| `./tests/unit/test_lm_eval_adapter.py` | Python | tests | lens:QA;type:테스트 | 포함 | - | 2026-01-28T17:56:20 | read-full | last:             adapter._ensure_lm_eval() | Python text file: Unit tests for LMEvalAdapter. | 내부 |
| `./tests/unit/test_markdown_report.py` | Python | tests | lens:QA;type:테스트 | 포함 | - | 2026-01-28T17:56:20 | read-full | last:         assert "**어휘 다양성이 낮음:**" in result | Python text file: Tests for MarkdownReportAdapter. | 내부 |
| `./tests/unit/test_memory_cache.py` | Python | tests | lens:QA;type:테스트 | 포함 | - | 2026-01-28T17:56:20 | read-full | last:         assert result is None | Python text file: Tests for Memory Cache Adapter. | 내부 |
| `./tests/unit/test_memory_services.py` | Python | tests | lens:QA;type:테스트 | 포함 | - | 2026-01-28T17:56:20 | read-full | last:     assert actions | Python text file: Tests for memory-aware evaluation and analysis helpers. | 내부 |
| `./tests/unit/test_method_plugins.py` | Python | tests | lens:QA;type:테스트 | 포함 | - | 2026-01-28T17:56:20 | read-full | last:     assert second_case.metadata\["method_missing_output"\] is True | Python text file: Tests for method plugin utilities. | 내부 |
| `./tests/unit/test_mlflow_tracker.py` | Python | tests | lens:QA;type:테스트 | 포함 | - | 2026-01-28T17:56:20 | read-full | last:             assert port_params == adapter_params, f"Method {method_name} signature mismatch" | Python text file: Unit tests for MLflow tracker adapter. | 내부 |
| `./tests/unit/test_model_config.py` | Python | tests | lens:QA;type:테스트 | 포함 | - | 2026-01-28T17:56:20 | read-full | last:         assert profile.embedding.model == "qwen3-embedding:0.6b" | Python text file: Unit tests for model configuration. | 내부 |
| `./tests/unit/test_nlp_adapter.py` | Python | tests | lens:QA;type:테스트 | 포함 | - | 2026-01-28T17:56:20 | read-full | last:         assert len(keywords) > 0 | Python text file: Tests for NLP analysis adapter. | 내부 |
| `./tests/unit/test_nlp_entities.py` | Python | tests | lens:QA;type:테스트 | 포함 | - | 2026-01-28T17:56:20 | read-full | last:         assert analysis_with_types.dominant_question_type == QuestionType.FACTUAL | Python text file: Tests for NLP analysis domain entities. | 내부 |
| `./tests/unit/test_ollama_adapter.py` | Python | tests | lens:QA;type:테스트 | 포함 | - | 2026-01-28T17:56:20 | read-full | last:         assert isinstance(adapter, OllamaAdapter) | Python text file: Unit tests for OllamaAdapter. | 내부 |
| `./tests/unit/test_openai_adapter.py` | Python | tests | lens:QA;type:테스트 | 포함 | - | 2026-01-28T17:56:20 | read-full | last:         assert total2 == 0 | Python text file: Tests for OpenAI LLM adapter. | 내부 |
| `./tests/unit/test_phoenix_adapter.py` | Python | tests | lens:QA;type:테스트 | 포함 | - | 2026-01-28T17:56:20 | read-full | last:         assert hasattr(tracker, "PhoenixAdapter") | Python text file: Unit tests for PhoenixAdapter. | 내부 |
| `./tests/unit/test_pipeline_orchestrator.py` | Python | tests | lens:QA;type:테스트 | 포함 | - | 2026-01-28T17:56:20 | read-full | last:         assert template.intent == AnalysisIntent.VERIFY_MORPHEME | Python text file: Phase 14.3: PipelineOrchestrator 단위 테스트. | 내부 |
| `./tests/unit/test_ports.py` | Python | tests | lens:QA;type:테스트 | 포함 | - | 2026-01-28T17:56:20 | read-full | last:         assert hints\["return"\] == EvaluationRun | Python text file: Port 인터페이스 정의 확인 테스트. | 내부 |
| `./tests/unit/test_postgres_storage.py` | Python | tests | lens:QA;type:테스트 | 포함 | - | 2026-01-28T17:56:20 | read-full | last:         assert cluster.representative_questions\[0\].startswith("보험료") | Python text file: Unit tests for PostgreSQL storage adapter. | 내부 |
| `./tests/unit/test_pr_comment_formatter.py` | Python | tests | lens:QA;type:테스트 | 포함 | - | 2026-01-28T17:56:20 | read-full | last:     assert "\| faithfulness \| 0.800 \| 0.820 \| +2.5% \| ✅ \|" in content | Python text file: test_pr_comment_formatter.py | 내부 |
| `./tests/unit/test_prompt_candidate_service.py` | Python | tests | lens:QA;type:테스트 | 포함 | - | 2026-01-28T17:56:20 | read-full | last:     assert candidates\[0\].content == "중복 테스트" | Python text file: test_prompt_candidate_service.py | 내부 |
| `./tests/unit/test_rag_trace_entities.py` | Python | tests | lens:QA;type:테스트 | 포함 | - | 2026-01-28T17:56:20 | read-full | last:         assert RerankMethod is not None | Python text file: Unit tests for RAG trace entities. | 내부 |
| `./tests/unit/test_regress_cli.py` | Python | tests | lens:QA;type:테스트 | 포함 | - | 2026-01-28T17:56:20 | read-full | last:     assert "regression" in result.stdout.lower() | Python text file: CLI tests for regress command. | 내부 |
| `./tests/unit/test_run_comparison_service.py` | Python | tests | lens:QA;type:테스트 | 포함 | - | 2026-01-28T17:56:20 | read-full | last:     assert isinstance(outcome.duration_ms, int) | Python text file: test_run_comparison_service.py | 내부 |
| `./tests/unit/test_run_memory_helpers.py` | Python | tests | lens:QA;type:테스트 | 포함 | - | 2026-01-28T17:56:20 | read-full | last:     assert kg.get_node_count() == 1 | Python text file: Tests for helper utilities in the run CLI module. | 내부 |
| `./tests/unit/test_run_mode_fixtures.py` | Python | tests | lens:QA;type:테스트 | 포함 | - | 2026-01-28T17:56:20 | read-full | last:     assert len(dataset.test_cases) >= 2 | Python text file: Fixture validation for run-mode regression datasets. | 내부 |
| `./tests/unit/test_settings.py` | Python | tests | lens:QA;type:테스트 | 포함 | - | 2026-01-28T17:56:20 | read-full | last:         Settings() | Python text file: Unit tests for settings configuration. | 내부 |
| `./tests/unit/test_sqlite_storage.py` | Python | tests | lens:QA;type:테스트 | 포함 | - | 2026-01-28T17:56:20 | read-full | last:         assert summary.thumb_up_rate is None | Python text file: Unit tests for SQLite storage adapter. | 내부 |
| `./tests/unit/test_stage_cli.py` | Python | tests | lens:QA;type:테스트 | 포함 | - | 2026-01-28T17:56:20 | read-full | last:     assert thresholds\["output.citation_count"\] == 2.0 | Python text file: CLI tests for stage commands. | 내부 |
| `./tests/unit/test_stage_event_schema.py` | Python | tests | lens:QA;type:테스트 | 포함 | - | 2026-01-28T17:56:20 | read-full | last:     assert event.stage_type == "retrieval" | Python text file: Unit tests for StageEvent schema normalization. | 내부 |
| `./tests/unit/test_stage_metric_service.py` | Python | tests | lens:QA;type:테스트 | 포함 | - | 2026-01-28T17:56:20 | read-full | last:     assert "order_reconstructed" not in precision_metric.evidence | Python text file: Unit tests for StageMetricService. | 내부 |
| `./tests/unit/test_stage_storage.py` | Python | tests | lens:QA;type:테스트 | 포함 | - | 2026-01-28T17:56:20 | read-full | last:     assert stored.evidence == {"relevant_count": 4} | Python text file: Unit tests for stage event storage in SQLite. | 내부 |
| `./tests/unit/test_stage_summary_service.py` | Python | tests | lens:QA;type:테스트 | 포함 | - | 2026-01-28T17:56:20 | read-full | last:     assert "output" in summary.missing_required_stage_types | Python text file: Unit tests for StageSummaryService. | 내부 |
| `./tests/unit/test_statistical_adapter.py` | Python | tests | lens:QA;type:테스트 | 포함 | - | 2026-01-28T17:56:20 | read-full | last:         assert any("correlation" in i.lower() for i in insights) | Python text file: Tests for Statistical Analysis Adapter. | 내부 |
| `./tests/unit/test_streaming_loader.py` | Python | tests | lens:QA;type:테스트 | 포함 | - | 2026-01-28T17:56:20 | read-full | last:         assert chunk_sizes == \[30, 30, 30, 10\] | Python text file: Tests for Streaming Dataset Loader. | 내부 |
| `./tests/unit/test_summary_eval_fixture.py` | Python | tests | lens:QA;type:테스트 | 포함 | - | 2026-01-28T17:56:20 | read-full | last:     assert mixed == 2 | Python text file: Tests for the summary evaluation minimal fixture. | 내부 |
| `./tests/unit/test_testset_generator.py` | Python | tests | lens:QA;type:테스트 | 포함 | - | 2026-01-28T17:56:20 | read-full | last:         assert "num_source_documents" in dataset.metadata | Python text file: Unit tests for testset generator. | 내부 |
| `./tests/unit/test_web_adapter.py` | Python | tests | lens:QA;type:테스트 | 포함 | - | 2026-01-28T17:56:20 | read-full | last:             assert hasattr(gate_result, "gap") | Python text file: Unit tests for Web API adapter. | 내부 |
| `./uv.lock` | Lock | infra | lens:운영;type:설정 | 포함 | - | 2026-01-28T17:56:20 | read-full | last: \] | Lock text file: uv.lock | 내부 |

## 4. Excluded Summary

### 4.1 탐색 중단(항상 제외) 디렉터리

아래 디렉터리는 SSoT 스크립트 실행 시 탐색이 중단되어 Raw List에 포함되지 않습니다:

<details>
<summary>제외된 디렉터리 목록 펼치기 (클릭)</summary>

```
./.git
./.pytest_cache
./.ruff_cache
./.venv
./__pycache__
./agent/__pycache__
./dist
./examples/usecase/__pycache__
./frontend/dist
./frontend/node_modules
./scratch/ragrefine/__pycache__
./scratch/ragrefine/agent/__pycache__
./scratch/ragrefine/agent/tools/__pycache__
./scratch/ragrefine/analysis/__pycache__
./scratch/ragrefine/cache/__pycache__
./scratch/ragrefine/data/__pycache__
./scratch/ragrefine/db/__pycache__
./scratch/ragrefine/experiments/__pycache__
./scratch/ragrefine/rag_expert_synth/__pycache__
./scratch/ragrefine/utils/__pycache__
./scripts/__pycache__
./scripts/docs/__pycache__
./scripts/docs/analyzer/__pycache__
./scripts/docs/models/__pycache__
./scripts/docs/renderer/__pycache__
./src/evalvault/__pycache__
./src/evalvault/adapters/__pycache__
./src/evalvault/adapters/inbound/__pycache__
./src/evalvault/adapters/inbound/api/__pycache__
./src/evalvault/adapters/inbound/api/routers/__pycache__
./src/evalvault/adapters/inbound/cli/__pycache__
./src/evalvault/adapters/inbound/cli/commands/__pycache__
./src/evalvault/adapters/inbound/cli/utils/__pycache__
./src/evalvault/adapters/inbound/mcp/__pycache__
./src/evalvault/adapters/outbound/__pycache__
./src/evalvault/adapters/outbound/analysis/__pycache__
./src/evalvault/adapters/outbound/benchmark/__pycache__
./src/evalvault/adapters/outbound/cache/__pycache__
./src/evalvault/adapters/outbound/dataset/__pycache__
./src/evalvault/adapters/outbound/debug/__pycache__
./src/evalvault/adapters/outbound/documents/__pycache__
./src/evalvault/adapters/outbound/documents/ocr/__pycache__
./src/evalvault/adapters/outbound/domain_memory/__pycache__
./src/evalvault/adapters/outbound/filesystem/__pycache__
./src/evalvault/adapters/outbound/improvement/__pycache__
./src/evalvault/adapters/outbound/kg/__pycache__
./src/evalvault/adapters/outbound/llm/__pycache__
./src/evalvault/adapters/outbound/methods/__pycache__
./src/evalvault/adapters/outbound/nlp/__pycache__
./src/evalvault/adapters/outbound/nlp/korean/__pycache__
./src/evalvault/adapters/outbound/phoenix/__pycache__
./src/evalvault/adapters/outbound/report/__pycache__
./src/evalvault/adapters/outbound/retriever/__pycache__
./src/evalvault/adapters/outbound/storage/__pycache__
./src/evalvault/adapters/outbound/tracer/__pycache__
./src/evalvault/adapters/outbound/tracker/__pycache__
./src/evalvault/config/__pycache__
./src/evalvault/domain/__pycache__
./src/evalvault/domain/entities/__pycache__
./src/evalvault/domain/metrics/__pycache__
./src/evalvault/domain/services/__pycache__
./src/evalvault/ports/__pycache__
./src/evalvault/ports/inbound/__pycache__
./src/evalvault/ports/outbound/__pycache__
./src/evalvault/reports/__pycache__
./src/evalvault/scripts/__pycache__
./tests/__pycache__
./tests/integration/__pycache__
./tests/integration/benchmark/__pycache__
./tests/unit/__pycache__
./tests/unit/adapters/inbound/mcp/__pycache__
./tests/unit/adapters/outbound/documents/__pycache__
./tests/unit/adapters/outbound/improvement/__pycache__
./tests/unit/adapters/outbound/kg/__pycache__
./tests/unit/adapters/outbound/retriever/__pycache__
./tests/unit/adapters/outbound/storage/__pycache__
./tests/unit/config/__pycache__
./tests/unit/domain/__pycache__
./tests/unit/domain/metrics/__pycache__
./tests/unit/domain/services/__pycache__
./tests/unit/reports/__pycache__
./tests/unit/scripts/__pycache__
```

</details>

### 4.2 실행 산출물 성격 디렉터리 (Raw List 포함, 본문 제외)

- `reports/analysis/`, `reports/comparison/`, `reports/**/artifacts/`, `data/db/`, `htmlcov/`
- 이 경로의 파일은 Raw List에는 포함되지만, 교과서 본편/부록의 상세 해설 대상에서는 제외로 표시합니다.
