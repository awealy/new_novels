// ==== 1️⃣ 填入你的 Supabase 项目信息 ====
const SUPABASE_URL = "https://hhxbcbmexxbrgwobwurl.supabase.co";
const SUPABASE_ANON_KEY = "sb_publishable_wlyylx3qSYE2F4qJiOaxGw_hcE467c2";
const supabase = window.supabase.createClient(SUPABASE_URL, SUPABASE_ANON_KEY);

// ==== 2️⃣ 填入你的 GitHub 仓库信息 ====
const GITHUB_REPO = "awealy/new-novels";
const GITHUB_TOKEN = "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"; // 需要 repo 权限

const novelsJsonUrl = `https://api.github.com/repos/${GITHUB_REPO}/contents/novels.json`;

document.getElementById("uploadBtn").addEventListener("click", async () => {
  const fileInput = document.getElementById("fileInput");
  if (!fileInput.files.length) {
    alert("请选择一个文件！");
    return;
  }

  const file = fileInput.files[0];
  const fileName = `${Date.now()}_${file.name}`;

  // 上传文件到 Supabase Storage
  const { data, error } = await supabase.storage
    .from("novels") // 👈 这里是你的 bucket 名
    .upload(fileName, file);

  if (error) {
    alert("上传失败：" + error.message);
    return;
  }

  const { data: publicUrlData } = supabase.storage
    .from("novels")
    .getPublicUrl(fileName);

  const fileUrl = publicUrlData.publicUrl;

  // 更新 novels.json 文件到 GitHub
  await updateNovelsJson({
    name: file.name,
    url: fileUrl,
    uploadedAt: new Date().toISOString(),
  });

  alert("上传成功！");
  loadNovels();
});

async function updateNovelsJson(newNovel) {
  const res = await fetch(novelsJsonUrl, {
    headers: { Authorization: `token ${GITHUB_TOKEN}` },
  });
  const data = await res.json();

  const content = atob(data.content);
  let novels = [];
  try {
    novels = JSON.parse(content);
  } catch {
    novels = [];
  }

  novels.unshift(newNovel);

  const updatedContent = btoa(JSON.stringify(novels, null, 2));

  await fetch(novelsJsonUrl, {
    method: "PUT",
    headers: {
      Authorization: `token ${GITHUB_TOKEN}`,
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      message: "Update novels.json",
      content: updatedContent,
      sha: data.sha,
    }),
  });
}

// ==== 3️⃣ 加载小说列表 ====
async function loadNovels() {
  const response = await fetch("novels.json?" + Date.now());
  const novels = await response.json();
  const listEl = document.getElementById("novelList");
  listEl.innerHTML = "";

  novels.forEach(novel => {
    const card = document.createElement("div");
    card.className = "novel-card";
    card.innerHTML = `
      <h3>${novel.name}</h3>
      <p>${new Date(novel.uploadedAt).toLocaleString()}</p>
      <a href="${novel.url}" target="_blank">阅读 / 下载</a>
    `;
    listEl.appendChild(card);
  });
}

loadNovels();
