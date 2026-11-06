"""Salidas ricas, errores y aislamiento del ejecutor documental local."""
from pathlib import Path
import os
import subprocess
import sys
import tempfile
import unittest
import nbformat

ROOT=Path(__file__).resolve().parents[1]


class NotebookExecutionTests(unittest.TestCase):
    def run_notebook(self,path):
        env=dict(os.environ,PYTHONUTF8='1',MPLBACKEND='Agg')
        return subprocess.run([sys.executable,str(ROOT/'scripts/execute_notebook_local.py'),str(path)],
            cwd=path.parent,env=env,capture_output=True,timeout=60)

    def test_streams_markdown_dataframe_figure_and_isolation(self):
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'notebook.ipynb'
            sources=["private_name=7\nprint('salida')",
                "from IPython.display import display,Markdown\ndisplay(Markdown('**texto**'))",
                "import pandas as pd\npd.DataFrame({'valor':[1,2]})",
                "%matplotlib inline\nimport matplotlib.pyplot as plt\nplt.plot([1,2]);plt.show()"]
            nbformat.write(nbformat.v4.new_notebook(cells=[nbformat.v4.new_code_cell(s) for s in sources]),path)
            result=self.run_notebook(path)
            self.assertEqual(result.returncode,0,result.stderr.decode(errors='replace')[-2000:])
            nb=nbformat.read(path,as_version=4)
            self.assertEqual([c.execution_count for c in nb.cells],[1,2,3,4])
            self.assertTrue(any(o.output_type=='stream' and 'salida' in o.text for o in nb.cells[0].outputs))
            self.assertTrue(any('text/markdown' in o.get('data',{}) for o in nb.cells[1].outputs))
            self.assertTrue(any('text/html' in o.get('data',{}) for o in nb.cells[2].outputs))
            self.assertTrue(any('image/png' in o.get('data',{}) for o in nb.cells[3].outputs))
            second=Path(directory)/'second.ipynb'
            nbformat.write(nbformat.v4.new_notebook(cells=[nbformat.v4.new_code_cell("assert 'private_name' not in globals()")]),second)
            self.assertEqual(self.run_notebook(second).returncode,0)

    def test_error_fails_without_replacing_notebook(self):
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'bad.ipynb'
            nbformat.write(nbformat.v4.new_notebook(cells=[nbformat.v4.new_code_cell("raise ValueError('fallo deliberado')")]),path)
            original=path.read_bytes()
            result=self.run_notebook(path)
            self.assertNotEqual(result.returncode,0)
            self.assertEqual(path.read_bytes(),original)


class OutputChannelTests(unittest.IsolatedAsyncioTestCase):
    async def test_waiting_output_does_not_block_event_loop(self):
        import asyncio
        sys.path.insert(0,str(ROOT/'scripts'))
        from execute_notebook_local import LocalOutputChannel
        channel=LocalOutputChannel()
        async def producer():
            await asyncio.sleep(.02)
            channel.call_handlers({'text':'listo'})
        producer_task=asyncio.create_task(producer())
        result=await asyncio.wait_for(channel.get_msg(timeout=1),timeout=2)
        self.assertEqual(result,{'text':'listo'})
        await producer_task


if __name__=='__main__':unittest.main()
