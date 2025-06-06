import { Button } from '@nextui-org/button';
import { Input } from '@nextui-org/input';
import React, { useState } from 'react';
import FolderIcon from './Icons/FolderIcon';
import FileLine from './FileLine';
import FileDetails from './FileDetails';
import WandIcon from './Icons/WandIcon';
import TelescopeButton from './TelescopeButton';
import UpdateSettings from './UpdateSettings';
import ollamaWave from '../../../assets/ollama_wave.gif';
import llamaFsLogo from '../../../assets/llama_fs.png';

const supportedFileTypes = [
  '.pdf',
  '.txt',
  '.png',
  '.jpg',
  '.jpeg',
  '.pptx',
  '.docx',
  '.xlsx',
];

function preorderTraversal(
  node: { name: string; children?: any[]; summary?: string; src_path?: string },
  prevfilename: string,
  depth: number,
  result: {
    filename: string;
    fullfilename: string;
    depth: number;
    summary?: string;
    src_path?: string;
  }[] = [],
) {
  result.push({
    filename: node.name,
    fullfilename: `${prevfilename}/${node.name}`,
    depth,
    summary: node.summary,
    src_path: node.src_path,
  });

  if (node.children) {
    node.children.forEach((child) => {
      preorderTraversal(
        child,
        `${prevfilename}/${node.name}`,
        depth + 1,
        result,
      );
    });
  }

  return result;
}

interface PathData {
  src_path: string;
  dst_path: string;
  summary: string;
}

interface TreeNode {
  name: string;
  children?: TreeNode[];
  summary?: string;
  src_path?: string;
}

interface FileData {
  filename: string;
  fullfilename: string;
  depth: number;
  summary?: string;
  src_path?: string;
}

function buildTree(paths: PathData[]) {
  const root: TreeNode = { name: 'root', children: [] };

  paths.forEach(({ src_path, dst_path, summary }) => {
    const parts = dst_path.split('/');
    let currentLevel = root.children;

    parts.forEach((part: string, index: number) => {
      let existingPath = currentLevel?.find((p: TreeNode) => p.name === part);

      if (!existingPath) {
        if (index === parts.length - 1) {
          // It's a file, include the summary and source path
          existingPath = { name: part, summary, src_path };
        } else {
          // It's a directory
          existingPath = { name: part, children: [] };
        }
        currentLevel?.push(existingPath);
      }

      if (existingPath.children) {
        currentLevel = existingPath.children;
      }
    });
  });

  return root;
}

function MainScreen() {
  const [watchMode, setWatchMode] = useState(false);
  const [selectedFile, setSelectedFile] = useState<FileData | null>(null);
  const [filePath, setFilePath] = useState(
    '/Users/stuartsaunders/Projects/llama-fs/sample_data',
  );
  const [loading, setLoading] = useState(false);

  // Function to handle file selection
  const handleFileSelect = (fileData: FileData) => {
    setSelectedFile(fileData);
  };

  const [newOldMap, setNewOldMap] = useState<PathData[]>([]);
  const [preOrderedFiles, setPreOrderedFiles] = useState<FileData[]>([]);
  // const preOrderedFiles = preorderTraversal(files, '', -1).slice(1);
  const [acceptedState, setAcceptedState] = React.useState<
    Record<string, boolean>
  >({});

  const handleBatch = async () => {
    setLoading(true);
    try {
      const response = await fetch('http://localhost:8000/batch', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          path: filePath,
          // path: '/Users/reibs/Projects/llama-fs/sample_data',
        }),
      });

      if (!response.ok) {
        throw new Error(
          `Server error: ${response.status} ${response.statusText}`,
        );
      }

      const data = await response.json();
      setNewOldMap(data);
      const treeData = buildTree(data);
      const preOrderedTreeData = preorderTraversal(treeData, '', -1).slice(1);
      setPreOrderedFiles(preOrderedTreeData);
      setAcceptedState(
        preOrderedTreeData.reduce(
          (acc, file) => ({ ...acc, [file.fullfilename]: false }),
          {},
        ),
      );
    } catch (error) {
      console.error('Failed to process batch:', error);
      let errorMessage = 'Unknown error occurred';

      if (error instanceof TypeError && error.message === 'Failed to fetch') {
        errorMessage =
          'Cannot connect to the server. Please ensure the FastAPI server is running on http://localhost:8000';
      } else if (error instanceof Error) {
        errorMessage = error.message;
      }

      alert(`Error: ${errorMessage}`);
    } finally {
      setLoading(false);
    }
  };
  const handleWatch = async () => {
    setLoading(true);
    try {
      const response = await fetch('http://localhost:8000/batch', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          path: filePath,
          // path: '/Users/reibs/Projects/llama-fs/sample_data',
        }),
      });

      if (!response.ok) {
        throw new Error(
          `Server error: ${response.status} ${response.statusText}`,
        );
      }
    } catch (error) {
      console.error('Failed to start watch mode:', error);
      let errorMessage = 'Unknown error occurred';

      if (error instanceof TypeError && error.message === 'Failed to fetch') {
        errorMessage =
          'Cannot connect to the server. Please ensure the FastAPI server is running on http://localhost:8000';
      } else if (error instanceof Error) {
        errorMessage = error.message;
      }

      alert(`Error: ${errorMessage}`);
    } finally {
      setLoading(false);
    }
  };

  const handleConfirmSelectedChanges = async () => {
    const returnedObj: Array<{
      base_path: string;
      src_path: string;
      dst_path: string;
    }> = [];
    preOrderedFiles.forEach((file) => {
      const isAccepted = acceptedState[file.fullfilename];
      if (isAccepted) {
        const noRootFileName = file.fullfilename.replace('/root/', '');
        if (newOldMap.some((change) => change.dst_path === noRootFileName)) {
          const acceptedChangeMap = newOldMap.find(
            (change) => change.dst_path === noRootFileName,
          );
          if (acceptedChangeMap) {
            returnedObj.push({
              base_path: filePath,
              src_path: acceptedChangeMap.src_path,
              dst_path: acceptedChangeMap.dst_path,
            });
          }
        }
      }
    });

    console.log(returnedObj);

    // commit endpoint only supports 1 change at a time
    const commitPromises = returnedObj.map(
      async (change: {
        base_path: string;
        src_path: string;
        dst_path: string;
      }) => {
        try {
          const response = await fetch('http://localhost:8000/commit', {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
            },
            body: JSON.stringify(change),
          });

          if (!response.ok) {
            throw new Error(
              `Server error: ${response.status} ${response.statusText}`,
            );
          }

          console.log('Commit successful:', response);
          return { success: true, change };
        } catch (error) {
          console.error('Failed to commit change:', error, change);
          return { success: false, change, error };
        }
      },
    );

    try {
      const results = await Promise.all(commitPromises);
      const failures = results.filter((result) => !result.success);

      if (failures.length > 0) {
        alert(
          `Failed to commit ${failures.length} out of ${results.length} changes. Check console for details.`,
        );
      } else {
        alert(`Successfully committed ${results.length} changes.`);
      }
    } catch (error) {
      console.error('Error processing commits:', error);
      alert('Error processing file changes. Check console for details.');
    }

    // clean objects
    setNewOldMap([]);
    setPreOrderedFiles([]);
    setAcceptedState({});
  };

  // Add the className 'dark' to main div to enable dark mode
  return (
    <div className="flex h-screen w-full">
      <div className="bg-gray-100 dark:bg-gray-800 border-r border-gray-200 dark:border-gray-700 p-4 flex flex-col gap-4">
        <div className="flex items-center gap-2">
          <FolderIcon className="h-6 w-6 text-gray-500 dark:text-gray-400" />
          <span className="font-medium text-gray-700 dark:text-gray-300">
            Llama-FS
          </span>
        </div>
        <nav className="flex flex-col gap-2">
          <div
            className="bg-white p-2 rounded cursor-pointer hover:bg-gray-100 transition-colors"
            onClick={() =>
              setFilePath('/Users/stuartsaunders/Projects/llama-fs/sample_data')
            }
          >
            /Users/stuartsaunders/Projects/llama-fs/sample_data
          </div>
          <div
            className="bg-white p-2 rounded cursor-pointer hover:bg-gray-100 transition-colors"
            onClick={() => setFilePath('/Users/stuartsaunders/Downloads')}
          >
            /Users/stuartsaunders/Downloads
          </div>
          <div
            className="bg-white p-2 rounded cursor-pointer hover:bg-gray-100 transition-colors"
            onClick={() => setFilePath('/Users/stuartsaunders/Desktop')}
          >
            /Users/stuartsaunders/Desktop
          </div>
        </nav>
      </div>
      <div className="flex-1 flex flex-col">
        <div className="bg-gray-100 dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700 p-4 flex items-center gap-4">
          <div className="flex items-center gap-2">
            <Input
              className="w-max rounded-lg"
              placeholder="Enter file path"
              type="text"
              onChange={(e) => setFilePath(e.target.value)}
              defaultValue="/Users/stuartsaunders/Projects/llama-fs/sample_data"
              value={filePath}
              style={{
                width: '400px',
              }}
            />
          </div>
          <div className="flex-1" />
          <div className="flex items-center gap-4">
            <Button variant="ghost" onClick={() => handleBatch()}>
              <WandIcon className="h-5 w-5 text-gray-600 dark:text-gray-400" />
            </Button>
            <div onClick={() => setWatchMode(!watchMode)}>
              <TelescopeButton isLoading={watchMode} />
            </div>
          </div>
        </div>
        <div className="flex-1 flex">
          <div
            className="w-1/2 overflow-auto p-4 space-y-2 border-r border-gray-200 dark:border-gray-700"
            style={{ maxHeight: 'calc(100vh - 4rem)' }}
          >
            {loading ? (
              // Existing loading block
              <div className="flex flex-col items-center">
                <h2 className="text-lg font-semibold mb-2">
                  Reading and classifying your files...
                </h2>
                <div className="flex justify-center" style={{ width: '50%' }}>
                  <img
                    src={ollamaWave}
                    alt="Loading..."
                    style={{ width: '100%' }}
                  />
                </div>
              </div>
            ) : preOrderedFiles.length === 0 ? (
              // Render llamaFsLogo and supported file types when not loading and no files
              <div
                className="flex flex-col items-center"
                style={{ height: '100%' }}
              >
                <h1 className="text-lg font-semibold mb-2">Llama-FS</h1>
                <p>Organize your drive with LLMs. </p>
                <div className="flex justify-center" style={{ width: '50%' }}>
                  <img
                    src={llamaFsLogo}
                    alt="Llama FS Logo"
                    style={{ width: '100%' }}
                  />
                </div>
                <p className="text-center mt-4">Supported file types:</p>
                <ul className="list-disc text-center">
                  {supportedFileTypes.map((type) => (
                    <li key={type}>{type}</li>
                  ))}
                </ul>
              </div>
            ) : (
              // Existing file details block
              <FileDetails fileData={selectedFile} />
            )}
            {preOrderedFiles.map((file) => (
              <div onClick={() => handleFileSelect(file)}>
                <FileLine
                  key={file.fullfilename}
                  filename={file.filename}
                  indentation={file.depth}
                  fullfilename={file.fullfilename}
                  acceptedState={acceptedState}
                  setAcceptedState={setAcceptedState}
                />
              </div>
            ))}
          </div>
          <div className="w-1/2 overflow-auto p-4 space-y-4">
            <FileDetails fileData={selectedFile} />
            <UpdateSettings />
            {/* Container for explaining the data in the file line that's selected */}
            {/* This container will be populated with content dynamically based on the selected FileLine */}
          </div>
        </div>
      </div>
      <div className="fixed inset-x-0 bottom-2 flex justify-center">
        <Button
          className="bg-green-300 text-gray-700 rounded p-3"
          onClick={() => handleConfirmSelectedChanges()}
        >
          Confirm selected changes
        </Button>
      </div>
    </div>
  );
}

export default MainScreen;
