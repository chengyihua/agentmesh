import fs from 'fs';
import path from 'path';
import matter from 'gray-matter';

// Assuming docs are in /web/docs
const docsDirectory = path.join(process.cwd(), 'docs');

export interface Doc {
  slug: string[];
  title: string;
  order: number;
  content: string;
  category: string;
  categoryOrder: number;
}

export interface NavItem {
  title: string;
  href: string;
}

export interface NavCategory {
  title: string;
  items: NavItem[];
  order: number;
}

export function getAllDocs(): Doc[] {
  const docs: Doc[] = [];

  if (!fs.existsSync(docsDirectory)) {
    return [];
  }

  const categories = fs.readdirSync(docsDirectory);

  for (const categoryDir of categories) {
    const categoryPath = path.join(docsDirectory, categoryDir);
    // Skip hidden files/dirs (like .DS_Store)
    if (categoryDir.startsWith('.')) continue;

    if (fs.statSync(categoryPath).isDirectory()) {
      const files = fs.readdirSync(categoryPath);
      
      for (const file of files) {
        if (file.endsWith('.md')) {
          const fullPath = path.join(categoryPath, file);
          const fileContents = fs.readFileSync(fullPath, 'utf8');
          const { data, content } = matter(fileContents);
          
          // Parse category name: "01-getting-started" -> "Getting Started"
          // Split by first hyphen to separate order
          const parts = categoryDir.split('-');
          const orderStr = parts[0];
          const namePart = parts.slice(1).join(' ');
          
          const categoryName = namePart.replace(/-/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
          const categoryOrder = parseInt(orderStr) || 99;

          // Parse slug: remove extension
          const fileName = file.replace(/\.md$/, '');
          const slug = [categoryDir, fileName];

          docs.push({
            slug,
            title: data.title || fileName,
            order: data.order || 99,
            content,
            category: categoryName,
            categoryOrder
          });
        }
      }
    }
  }

  return docs.sort((a, b) => {
    if (a.categoryOrder !== b.categoryOrder) return a.categoryOrder - b.categoryOrder;
    return a.order - b.order;
  });
}

export function getDocBySlug(slug: string[]): Doc | null {
  try {
    const fullPath = path.join(docsDirectory, ...slug) + '.md';
    if (!fs.existsSync(fullPath)) return null;
    
    const fileContents = fs.readFileSync(fullPath, 'utf8');
    const { data, content } = matter(fileContents);
    
    const categoryDir = slug[0];
    const parts = categoryDir.split('-');
    const orderStr = parts[0];
    const namePart = parts.slice(1).join(' ');
    
    const categoryName = namePart.replace(/-/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
    const categoryOrder = parseInt(orderStr) || 99;

    return {
      slug,
      title: data.title || slug[slug.length - 1],
      order: data.order || 99,
      content,
      category: categoryName,
      categoryOrder
    };
  } catch (e) {
    return null;
  }
}

export function getNavigation(): NavCategory[] {
  const docs = getAllDocs();
  const categories: Record<string, NavCategory> = {};

  docs.forEach(doc => {
    if (!categories[doc.category]) {
      categories[doc.category] = {
        title: doc.category,
        items: [],
        order: doc.categoryOrder
      };
    }
    categories[doc.category].items.push({
      title: doc.title,
      href: `/guide/${doc.slug.join('/')}`
    });
  });

  return Object.values(categories).sort((a, b) => a.order - b.order);
}
