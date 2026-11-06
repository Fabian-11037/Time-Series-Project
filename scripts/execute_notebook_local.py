"""Ejecuta un cuaderno con nbclient e IPython local, sin puertos TCP.

El proceso se crea por cuaderno desde run_eda.py para aislar su estado.
"""
import argparse
import asyncio
import os
from queue import Empty
from pathlib import Path
import nbformat
from nbclient import NotebookClient
from ipykernel.inprocess.manager import InProcessKernelManager
from ipykernel.inprocess.blocking import BlockingInProcessKernelClient, BlockingInProcessChannel
from traitlets import Type


class LocalOutputChannel(BlockingInProcessChannel):
    async def get_msg(self, block=True, timeout=None):
        # Una espera de Queue bloqueante impediría que nbclient procese respuestas.
        loop=asyncio.get_running_loop()
        deadline=None if timeout is None else loop.time()+timeout
        while True:
            try:
                return self._in_queue.get_nowait()
            except Empty:
                if not block or (deadline is not None and loop.time()>=deadline):
                    raise
                await asyncio.sleep(.005)


class LocalNotebookClient(BlockingInProcessKernelClient):
    iopub_channel_class=Type(LocalOutputChannel)

    def wait_for_ready(self, timeout=None):
        if self.kernel is None:
            raise RuntimeError('El kernel local no se inició.')
        # La construcción del kernel es síncrona y no requiere handshake TCP.
        return None

    def execute(self, code, **kwargs):
        # nbclient comprueba el error en la respuesta del kernel.
        kwargs.pop('stop_on_error', None)
        return super().execute(code, **kwargs)

    def _dispatch_to_kernel(self, msg):
        # El kernel local redirige IO después de asignar el padre de la petición.
        self.kernel.stdout.set_parent(msg)
        self.kernel.stderr.set_parent(msg)
        return super()._dispatch_to_kernel(msg)


class LocalNotebookManager(InProcessKernelManager):
    def shutdown_kernel(self, now=False, **kwargs):
        return super().shutdown_kernel()

    def client(self, **kwargs):
        return LocalNotebookClient(kernel=self.kernel, parent=self,
            session=self.session, **kwargs)


def execute_notebook(path):
    if os.name=='nt':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    path=Path(path)
    nb=nbformat.read(path,as_version=4)
    client=NotebookClient(nb,kernel_manager_class=LocalNotebookManager,
        timeout=1800,resources={'metadata':{'path':str(path.parent)}})
    client.execute()
    with path.open('w',encoding='utf-8',newline='\n') as stream:
        nbformat.write(nb,stream)


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('notebook',type=Path)
    execute_notebook(parser.parse_args().notebook.resolve())
