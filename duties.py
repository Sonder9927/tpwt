from duty import duty
from duty.callables import mkdocs


@duty
def docs(ctx):
    ctx.run(mkdocs.build(strict=True), title="Building documentation")
