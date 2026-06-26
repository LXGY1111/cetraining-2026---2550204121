const fs = require('fs');
  const path = require('path');
  const readline = require('readline');

  /**
   * 统计文本文件中每个单词出现的次数（修复版）
   * @param {string} inputFilePath - 输入文本文件的路径
   * @param {string} outputFilePath - 输出文件的路径
   * @param {Object} options - 配置选项
   * @param {boolean} options.filterNumbers - 是否过滤纯数字
   * @param {boolean} options.filterStopWords - 是否过滤停用词
   * @returns {Promise<boolean>} - 成功返回true，失败返回false
   */
  async function countWordsInFile(inputFilePath, outputFilePath, options = {}) {
      const { filterNumbers = true, filterStopWords = false } = options;

      // 常见英文停用词
      const stopWords = new Set([
          'the', 'be', 'to', 'of', 'and', 'a', 'in', 'that', 'have', 'i',
          'it', 'for', 'not', 'on', 'with', 'he', 'as', 'you', 'do', 'at',
          'this', 'but', 'his', 'by', 'from', 'they', 'we', 'say', 'her', 'she',
          'or', 'an', 'will', 'my', 'one', 'all', 'would', 'there', 'their',
          'what', 'so', 'up', 'out', 'if', 'about', 'who', 'get', 'which', 'go'
      ]);

      try {
          // 检查文件是否存在
          if (!fs.existsSync(inputFilePath)) {
              console.error(`错误: 输入文件不存在: ${inputFilePath}`);
              return false;
          }

          // 检查文件大小，决定处理方式
          const stats = fs.statSync(inputFilePath);
          const fileSizeMB = stats.size / (1024 * 1024);

          console.log(`文件大小: ${fileSizeMB.toFixed(2)} MB`);

          // 大文件使用流式处理（>10MB）
          if (fileSizeMB > 10) {
              console.log('使用流式处理...');
              return await processWithStream(inputFilePath, outputFilePath, { filterNumbers, filterStopWords, stopWords });
          }

          console.log('使用内存处理...');
          // 小文件使用内存处理
          const content = await fs.promises.readFile(inputFilePath, 'utf-8');

          // 改进的正则表达式，支持Unicode字符和连字符
          const words = content.toLowerCase()
              .replace(/[^\p{L}\p{N}\s'-]/gu, ' ')  // 保留Unicode字母、数字、空格、连字符、撇号
              .split(/\s+/)
              .filter(word => {
                  if (word.length === 0) return false;
                  if (filterNumbers && /^\d+$/.test(word)) return false; // 过滤纯数字
                  if (filterStopWords && stopWords.has(word)) return false; // 过滤停用词
                  return true;
              });

          // 统计单词出现次数
          const wordCount = {};
          for (const word of words) {
              wordCount[word] = (wordCount[word] || 0) + 1;
          }

          // 保存结果
          return await saveResults(wordCount, outputFilePath, words.length);
      } catch (error) {
          console.error('处理文件时出错:', error.message);
          return false;
      }
  }

  /**
   * 流式处理大文件
   */
  async function processWithStream(inputFilePath, outputFilePath, options) {
      const { filterNumbers, filterStopWords, stopWords } = options;
      const wordCount = {};
      let totalWords = 0;
      let lineCount = 0;

      const fileStream = fs.createReadStream(inputFilePath, { encoding: 'utf-8' });
      const rl = readline.createInterface({
          input: fileStream,
          crlfDelay: Infinity
      });

      console.log('开始流式处理...');

      for await (const line of rl) {
          lineCount++;
          const words = line.toLowerCase()
              .replace(/[^\p{L}\p{N}\s'-]/gu, ' ')
              .split(/\s+/)
              .filter(word => {
                  if (word.length === 0) return false;
                  if (filterNumbers && /^\d+$/.test(word)) return false;
                  if (filterStopWords && stopWords.has(word)) return false;
                  return true;
              });

          totalWords += words.length;

          for (const word of words) {
              wordCount[word] = (wordCount[word] || 0) + 1;
          }

          // 每处理1000行显示进度
          if (lineCount % 1000 === 0) {
              console.log(`已处理 ${lineCount} 行，发现 ${Object.keys(wordCount).length} 个不同单词`);
          }
      }

      console.log(`处理完成：共 ${lineCount} 行，${totalWords} 个单词`);

      // 保存结果
      return await saveResults(wordCount, outputFilePath, totalWords);
  }

  /**
   * 保存统计结果到文件
   */
  async function saveResults(wordCount, outputFilePath, totalWords) {
      try {
          // 按出现次数降序排序
          const sortedWords = Object.entries(wordCount)
              .sort((a, b) => b[1] - a[1] || a[0].localeCompare(b[0]));

          const uniqueWords = sortedWords.length;

          // 准备输出内容
          let outputContent = `单词统计结果 (共 ${totalWords} 个单词，${uniqueWords} 个不同单词)\n`;
          outputContent += `生成时间: ${new Date().toLocaleString()}\n`;
          outputContent += `=========================================\n\n`;

          // 前20个最常见单词
          outputContent += `前20个最常见单词:\n`;
          outputContent += `-----------------------------------------\n`;
          const top20 = sortedWords.slice(0, 20);
          for (const [word, count] of top20) {
              const percentage = ((count / totalWords) * 100).toFixed(2);
              outputContent += `${word.padEnd(20)}: ${count.toString().padStart(6)} (${percentage}%)\n`;
          }

          outputContent += `\n完整统计结果:\n`;
          outputContent += `-----------------------------------------\n`;
          for (const [word, count] of sortedWords) {
              outputContent += `${word}: ${count}\n`;
          }

          // 确保输出目录存在
          const outputDir = path.dirname(outputFilePath);
          if (!fs.existsSync(outputDir)) {
              await fs.promises.mkdir(outputDir, { recursive: true });
          }

          // 写入输出文件
          await fs.promises.writeFile(outputFilePath, outputContent, 'utf-8');

          console.log(`统计完成！结果已保存到: ${outputFilePath}`);
          console.log(`总计: ${totalWords} 个单词, ${uniqueWords} 个不同单词`);

          // 显示前5个最常见单词
          console.log(`\n前5个最常见单词:`);
          top20.slice(0, 5).forEach(([word, count], index) => {
              const percentage = ((count / totalWords) * 100).toFixed(2);
              console.log(`  ${index + 1}. ${word}: ${count} 次 (${percentage}%)`);
          });

          return true;
      } catch (error) {
          console.error('保存结果时出错:', error.message);
          return false;
      }
  }

  /**
   * 命令行接口函数
   * @param {string[]} args - 命令行参数
   */
  async function main(args) {
      console.log('单词统计工具 v2.0 (修复版)');
      console.log('==========================\n');

      // 解析命令行选项
      const options = {
          filterNumbers: !args.includes('--include-numbers'),
          filterStopWords: args.includes('--no-stopwords')
      };

      // 过滤掉选项参数，获取文件路径
      const fileArgs = args.filter(arg => !arg.startsWith('--'));

      if (fileArgs.length !== 2) {
          console.log('用法: node word_counter.js [选项] <输入文件> <输出文件>');
          console.log('\n选项:');
          console.log('  --include-numbers    包含纯数字统计（默认过滤）');
          console.log('  --no-stopwords       过滤常见停用词');
          console.log('\n示例:');
          console.log('  node word_counter.js input.txt output.txt');
          console.log('  node word_counter.js --include-numbers input.txt output.txt');
          console.log('  node word_counter.js --no-stopwords input.txt C:\\Users\\流星\\Desktop\\bbbb\\word_count.txt');
          return;
      }

      const inputFilePath = fileArgs[0];
      const outputFilePath = fileArgs[1];

      const success = await countWordsInFile(inputFilePath, outputFilePath, options);
      if (!success) {
          console.error('单词统计失败');
          process.exit(1);  // 修复：第78行缺失的错误处理
      }
  }

  // 如果直接运行此脚本，则执行主函数
  if (require.main === module) {
      const args = process.argv.slice(2);
      main(args).catch(error => {
          console.error('程序执行出错:', error);
          process.exit(1);
      });
  }

  // 导出函数供其他模块调用
  module.exports = {
      countWordsInFile,
      processWithStream,
      saveResults,
      main
  };const fs = require('fs');
  const path = require('path');
  const readline = require('readline');

  /**
   * 统计文本文件中每个单词出现的次数（修复版）
   * @param {string} inputFilePath - 输入文本文件的路径
   * @param {string} outputFilePath - 输出文件的路径
   * @param {Object} options - 配置选项
   * @param {boolean} options.filterNumbers - 是否过滤纯数字
   * @param {boolean} options.filterStopWords - 是否过滤停用词
   * @returns {Promise<boolean>} - 成功返回true，失败返回false
   */
  async function countWordsInFile(inputFilePath, outputFilePath, options = {}) {
      const { filterNumbers = true, filterStopWords = false } = options;

      // 常见英文停用词
      const stopWords = new Set([
          'the', 'be', 'to', 'of', 'and', 'a', 'in', 'that', 'have', 'i',
          'it', 'for', 'not', 'on', 'with', 'he', 'as', 'you', 'do', 'at',
          'this', 'but', 'his', 'by', 'from', 'they', 'we', 'say', 'her', 'she',
          'or', 'an', 'will', 'my', 'one', 'all', 'would', 'there', 'their',
          'what', 'so', 'up', 'out', 'if', 'about', 'who', 'get', 'which', 'go'
      ]);

      try {
          // 检查文件是否存在
          if (!fs.existsSync(inputFilePath)) {
              console.error(`错误: 输入文件不存在: ${inputFilePath}`);
              return false;
          }

          // 检查文件大小，决定处理方式
          const stats = fs.statSync(inputFilePath);
          const fileSizeMB = stats.size / (1024 * 1024);

          console.log(`文件大小: ${fileSizeMB.toFixed(2)} MB`);

          // 大文件使用流式处理（>10MB）
          if (fileSizeMB > 10) {
              console.log('使用流式处理...');
              return await processWithStream(inputFilePath, outputFilePath, { filterNumbers, filterStopWords, stopWords });
          }

          console.log('使用内存处理...');
          // 小文件使用内存处理
          const content = await fs.promises.readFile(inputFilePath, 'utf-8');

          // 改进的正则表达式，支持Unicode字符和连字符
          const words = content.toLowerCase()
              .replace(/[^\p{L}\p{N}\s'-]/gu, ' ')  // 保留Unicode字母、数字、空格、连字符、撇号
              .split(/\s+/)
              .filter(word => {
                  if (word.length === 0) return false;
                  if (filterNumbers && /^\d+$/.test(word)) return false; // 过滤纯数字
                  if (filterStopWords && stopWords.has(word)) return false; // 过滤停用词
                  return true;
              });

          // 统计单词出现次数
          const wordCount = {};
          for (const word of words) {
              wordCount[word] = (wordCount[word] || 0) + 1;
          }

          // 保存结果
          return await saveResults(wordCount, outputFilePath, words.length);
      } catch (error) {
          console.error('处理文件时出错:', error.message);
          return false;
      }
  }

  /**
   * 流式处理大文件
   */
  async function processWithStream(inputFilePath, outputFilePath, options) {
      const { filterNumbers, filterStopWords, stopWords } = options;
      const wordCount = {};
      let totalWords = 0;
      let lineCount = 0;

      const fileStream = fs.createReadStream(inputFilePath, { encoding: 'utf-8' });
      const rl = readline.createInterface({
          input: fileStream,
          crlfDelay: Infinity
      });

      console.log('开始流式处理...');

      for await (const line of rl) {
          lineCount++;
          const words = line.toLowerCase()
              .replace(/[^\p{L}\p{N}\s'-]/gu, ' ')
              .split(/\s+/)
              .filter(word => {
                  if (word.length === 0) return false;
                  if (filterNumbers && /^\d+$/.test(word)) return false;
                  if (filterStopWords && stopWords.has(word)) return false;
                  return true;
              });

          totalWords += words.length;

          for (const word of words) {
              wordCount[word] = (wordCount[word] || 0) + 1;
          }

          // 每处理1000行显示进度
          if (lineCount % 1000 === 0) {
              console.log(`已处理 ${lineCount} 行，发现 ${Object.keys(wordCount).length} 个不同单词`);
          }
      }

      console.log(`处理完成：共 ${lineCount} 行，${totalWords} 个单词`);

      // 保存结果
      return await saveResults(wordCount, outputFilePath, totalWords);
  }

  /**
   * 保存统计结果到文件
   */
  async function saveResults(wordCount, outputFilePath, totalWords) {
      try {
          // 按出现次数降序排序
          const sortedWords = Object.entries(wordCount)
              .sort((a, b) => b[1] - a[1] || a[0].localeCompare(b[0]));

          const uniqueWords = sortedWords.length;

          // 准备输出内容
          let outputContent = `单词统计结果 (共 ${totalWords} 个单词，${uniqueWords} 个不同单词)\n`;
          outputContent += `生成时间: ${new Date().toLocaleString()}\n`;
          outputContent += `=========================================\n\n`;

          // 前20个最常见单词
          outputContent += `前20个最常见单词:\n`;
          outputContent += `-----------------------------------------\n`;
          const top20 = sortedWords.slice(0, 20);
          for (const [word, count] of top20) {
              const percentage = ((count / totalWords) * 100).toFixed(2);
              outputContent += `${word.padEnd(20)}: ${count.toString().padStart(6)} (${percentage}%)\n`;
          }

          outputContent += `\n完整统计结果:\n`;
          outputContent += `-----------------------------------------\n`;
          for (const [word, count] of sortedWords) {
              outputContent += `${word}: ${count}\n`;
          }

          // 确保输出目录存在
          const outputDir = path.dirname(outputFilePath);
          if (!fs.existsSync(outputDir)) {
              await fs.promises.mkdir(outputDir, { recursive: true });
          }

          // 写入输出文件
          await fs.promises.writeFile(outputFilePath, outputContent, 'utf-8');

          console.log(`统计完成！结果已保存到: ${outputFilePath}`);
          console.log(`总计: ${totalWords} 个单词, ${uniqueWords} 个不同单词`);

          // 显示前5个最常见单词
          console.log(`\n前5个最常见单词:`);
          top20.slice(0, 5).forEach(([word, count], index) => {
              const percentage = ((count / totalWords) * 100).toFixed(2);
              console.log(`  ${index + 1}. ${word}: ${count} 次 (${percentage}%)`);
          });

          return true;
      } catch (error) {
          console.error('保存结果时出错:', error.message);
          return false;
      }
  }

  /**
   * 命令行接口函数
   * @param {string[]} args - 命令行参数
   */
  async function main(args) {
      console.log('单词统计工具 v2.0 (修复版)');
      console.log('==========================\n');

      // 解析命令行选项
      const options = {
          filterNumbers: !args.includes('--include-numbers'),
          filterStopWords: args.includes('--no-stopwords')
      };

      // 过滤掉选项参数，获取文件路径
      const fileArgs = args.filter(arg => !arg.startsWith('--'));

      if (fileArgs.length !== 2) {
          console.log('用法: node word_counter.js [选项] <输入文件> <输出文件>');
          console.log('\n选项:');
          console.log('  --include-numbers    包含纯数字统计（默认过滤）');
          console.log('  --no-stopwords       过滤常见停用词');
          console.log('\n示例:');
          console.log('  node word_counter.js input.txt output.txt');
          console.log('  node word_counter.js --include-numbers input.txt output.txt');
          console.log('  node word_counter.js --no-stopwords input.txt C:\\Users\\流星\\Desktop\\bbbb\\word_count.txt');
          return;
      }

      const inputFilePath = fileArgs[0];
      const outputFilePath = fileArgs[1];

      const success = await countWordsInFile(inputFilePath, outputFilePath, options);
      if (!success) {
          console.error('单词统计失败');
          process.exit(1);  // 修复：第78行缺失的错误处理
      }
  }

  // 如果直接运行此脚本，则执行主函数
  if (require.main === module) {
      const args = process.argv.slice(2);
      main(args).catch(error => {
          console.error('程序执行出错:', error);
          process.exit(1);
      });
  }

  // 导出函数供其他模块调用
  module.exports = {
      countWordsInFile,
      processWithStream,
      saveResults,
      main
  };