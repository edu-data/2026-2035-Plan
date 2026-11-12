import { removeBackground } from '@imgly/background-removal-node';
import fs from 'fs'; import path from 'path'; import { pathToFileURL } from 'url';
const [,, inDir, outDir] = process.argv;
for (const n of ['nuna','jong','dog']) {
  const src = pathToFileURL(path.join(inDir, n + '.png')).href;
  const blob = await removeBackground(src, { model: 'medium', output: { format: 'image/png', quality: 1 } });
  fs.writeFileSync(path.join(outDir, n + '_cut.png'), Buffer.from(await blob.arrayBuffer()));
  console.log('ok', n);
}
