# Exinc

Tool to expand C++ includes for competitive programmers.

## Installation

> From `pip`:
> ```console
> $ pip install exinc
> ```

> From source:
> ```console
> $ pip install .
> ```

## Configuration

Run the tool one first time for it to create a default configuration.

```console
$ exinc --help
```

Now you'll find a configuration file in `/home/$USER/.exinc` that you can edit.

## Usage

First, you have to properly place the files you want to include. You should either:

1. Put them in the same folder of your to-be-compiled source code;
2. Or put them somewhere, and add such path to `DEFAULT_PATHS` in the `.exinc` configuration file.

Notice that when you go with (2), you also have to make sure you add this path to other places of interest. For instance, when using `vscode`, you also want to make sure IntelliSense will recognize these headers.

Now, you can write C++-based solutions and use your newly available includes:

```cpp
// MyIncludedCode.cpp
int included_function() {
  return 42;
}
```

```cpp
// solution.cpp
#include "MyIncludedCode.cpp"
#include <bits/stdc++.h>

int32_t main() {
  cout << included_function() << endl;
  // Code should compile, and print 42.
}
```

Ultimately, this code will be expanded by Exinc to:

```cpp
// solution.pre.cpp
int included_function() {
  return 42;
}
#include <bits/stdc++.h>

int32_t main() {
  cout << included_function() << endl;
  // Code should compile, and print 42.
}
```