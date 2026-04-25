# Python pathlib Module

## Overview
Object-oriented filesystem paths.

```python
from pathlib import Path
```

## Constructing Paths
```python
p = Path('docs') / 'conf.py'
p = Path('/etc').joinpath('passwd')
p = Path.home()
p = Path.cwd()
```

## Path Properties
```python
p = Path('/usr/bin/python3')
p.parts          # ('/', 'usr', 'bin', 'python3')
p.parent         # PosixPath('/usr/bin')
p.name           # 'python3'
p.stem           # 'python3'
p.suffix         # ''

p = Path('my/library.tar.gz')
p.stem           # 'library.tar'
p.suffix         # '.gz'
p.suffixes       # ['.tar', '.gz']
```

## Checking Paths
```python
p.exists()
p.is_file()
p.is_dir()
p.is_symlink()
p.is_absolute()
```

## File I/O
```python
content = p.read_text(encoding='utf-8')
data = p.read_bytes()
p.write_text('Text file contents')
p.write_bytes(b'Binary file contents')

with p.open() as f:
    line = f.readline()
```

## Path Resolution
```python
p.resolve()       # Resolves symlinks and '..'
p.absolute()      # Makes absolute
p.expanduser()    # Expands '~'
```

## Manipulating Paths
```python
p.with_name('setup.py')
p.with_stem('lib')
p.with_suffix('.bz2')
p.relative_to('/usr')
```

## Directory Operations
```python
for child in p.iterdir():
    print(child)

list(p.glob('*.py'))
list(p.glob('**/*.py'))      # Recursive
list(p.rglob('*.py'))        # Same as above
```

## Creating Files & Directories
```python
p.touch()                           # Create empty file
p.mkdir(parents=True, exist_ok=True)  # Create directory
```

## File Operations
```python
p.unlink()                    # Delete file
p.unlink(missing_ok=True)    # Don't raise if missing
d.rmdir()                    # Delete empty directory
p.rename('bar')              # Rename
p.replace('bar')             # Replace existing target
```

## File Information
```python
stat = p.stat()
stat.st_size      # File size
stat.st_mtime     # Modification time
```

## Comparison with os/os.path

| os/os.path | pathlib |
|-----------|---------|
| `os.path.dirname()` | `Path.parent` |
| `os.path.basename()` | `Path.name` |
| `os.path.splitext()` | `Path.stem`, `Path.suffix` |
| `os.path.join()` | `Path / operator` |
| `os.path.abspath()` | `Path.absolute()` |
| `os.listdir()` | `Path.iterdir()` |
| `os.mkdir()` | `Path.mkdir()` |
