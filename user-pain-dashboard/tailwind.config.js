/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        // 浅色系主色调
        page: {
          bg: '#FAFAFA',
          card: '#FFFFFF',
          border: '#E5E5E5',
        },
        text: {
          primary: '#1A1A1A',
          secondary: '#666666',
          muted: '#999999',
          link: '#4A90A4',
        },
        // 低饱和度强调色
        accent: {
          blue: '#6B8FA3',
          green: '#7BA37B',
          orange: '#C4956A',
          red: '#B87878',
        },
        // 严重程度
        severity: {
          high: '#C75050',
          medium: '#C49A4A',
          low: '#6B9B6B',
        },
        // 分类标签色（极低饱和度）
        tag: {
          feature: '#E8EEF2',
          performance: '#F2EEE8',
          ux: '#EEF2E8',
          bug: '#F2E8E8',
          privacy: '#EEE8F2',
        },
      },
      fontFamily: {
        sans: ['-apple-system', 'BlinkMacSystemFont', 'PingFang SC', 'Helvetica Neue', 'sans-serif'],
      },
      fontSize: {
        'page-title': ['32px', { fontWeight: '600', lineHeight: '1.3' }],
        'section-title': ['20px', { fontWeight: '600', lineHeight: '1.4' }],
        'card-title': ['16px', { fontWeight: '500', lineHeight: '1.5' }],
        'body': ['14px', { fontWeight: '400', lineHeight: '1.6' }],
        'caption': ['12px', { fontWeight: '400', lineHeight: '1.5' }],
      },
      boxShadow: {
        'card': '0 1px 3px rgba(0,0,0,0.04), 0 1px 2px rgba(0,0,0,0.02)',
        'card-hover': '0 4px 12px rgba(0,0,0,0.06)',
      },
      animation: {
        'fade-in': 'fadeIn 0.2s ease-out',
      },
      keyframes: {
        fadeIn: {
          '0%': { opacity: '0', transform: 'translateY(4px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
      },
    },
  },
  plugins: [],
}
