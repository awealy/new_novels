export default async function handler(req, res) {
  if (req.method !== 'POST') return res.status(405).json({ message: 'Method not allowed' });

  const { filename, content, username } = req.body;

  const GITHUB_TOKEN = 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;
  const REPO = 'awealy/new_novels';
  const BRANCH = 'main';
  const PATH = `submissions/${filename}`;

  try {
    const response = await fetch(`https://api.github.com/repos/${REPO}/contents/${PATH}`, {
      method: 'PUT',
      headers: {
        Authorization: `Bearer ${GITHUB_TOKEN}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        message: `投稿: ${filename} by ${username}`,
        content: content,
        branch: BRANCH,
      }),
    });

    const data = await response.json();
    if (response.ok) {
      res.status(200).json({ message: 'Upload success', url: data.content.html_url });
    } else {
      res.status(400).json(data);
    }
  } catch (err) {
    res.status(500).json({ message: err.message });
  }
}
