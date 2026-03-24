(function (window, document) {
  'use strict';

  function getTargetFromTrigger(trigger) {
    if (!trigger) return null;
    var selector = trigger.getAttribute('data-bs-target') || trigger.getAttribute('href');
    if (!selector || selector === '#') return null;
    try {
      return document.querySelector(selector);
    } catch (err) {
      return null;
    }
  }

  function hideAllDropdowns(exceptToggle) {
    var menus = document.querySelectorAll('.dropdown-menu.show');
    menus.forEach(function (menu) {
      var parent = menu.closest('.dropdown');
      var toggle = parent ? parent.querySelector('[data-bs-toggle="dropdown"]') : null;
      if (exceptToggle && toggle === exceptToggle) return;
      menu.classList.remove('show');
      if (parent) parent.classList.remove('show');
      if (toggle) toggle.setAttribute('aria-expanded', 'false');
    });
  }

  function findDropdownMenu(toggle) {
    if (!toggle) return null;
    var parent = toggle.closest('.dropdown');
    if (parent) {
      var inParent = parent.querySelector('.dropdown-menu');
      if (inParent) return inParent;
    }
    var next = toggle.nextElementSibling;
    if (next && next.classList.contains('dropdown-menu')) {
      return next;
    }
    return null;
  }

  function positionDropdownMenu(toggle, menu) {
    if (!toggle || !menu) return;

    menu.setAttribute('data-bs-popper', 'static');
    menu.style.maxWidth = Math.max(220, window.innerWidth - 16) + 'px';

    if (menu.classList.contains('dropdown-menu-end')) {
      menu.style.left = 'auto';
      menu.style.right = '0';
    } else {
      menu.style.left = '0';
      menu.style.right = 'auto';
    }

    menu.style.top = 'calc(100% + 0.5rem)';

    var rect = menu.getBoundingClientRect();
    if (rect.right > window.innerWidth - 8) {
      menu.style.right = '0.5rem';
      menu.style.left = 'auto';
    }

    rect = menu.getBoundingClientRect();
    if (rect.left < 8) {
      menu.style.left = '0.5rem';
      menu.style.right = 'auto';
    }
  }

  function createModalInstance(element) {
    return {
      _element: element,
      show: function () {
        if (!this._element) return;
        this._element.style.display = 'block';
        this._element.classList.add('show');
        this._element.removeAttribute('aria-hidden');

        if (!document.querySelector('.offline-backdrop')) {
          var backdrop = document.createElement('div');
          backdrop.className = 'modal-backdrop fade show offline-backdrop';
          document.body.appendChild(backdrop);
        }
        document.body.classList.add('modal-open');
      },
      hide: function () {
        if (!this._element) return;
        this._element.classList.remove('show');
        this._element.style.display = 'none';
        this._element.setAttribute('aria-hidden', 'true');

        var backdrops = document.querySelectorAll('.offline-backdrop');
        backdrops.forEach(function (item) {
          item.remove();
        });
        document.body.classList.remove('modal-open');
      }
    };
  }

  if (typeof window.bootstrap === 'undefined') {
    var modalInstances = new WeakMap();
    var dropdownInstances = new WeakMap();
    var collapseInstances = new WeakMap();

    function Modal(element) {
      var instance = createModalInstance(element);
      if (element) {
        modalInstances.set(element, instance);
      }
      return instance;
    }

    Modal.getInstance = function (element) {
      return modalInstances.get(element) || null;
    };

    Modal.getOrCreateInstance = function (element) {
      return Modal.getInstance(element) || new Modal(element);
    };

    function Alert(element) {
      return {
        close: function () {
          if (element && element.parentNode) {
            element.parentNode.removeChild(element);
          }
        }
      };
    }

    function Dropdown(toggleElement) {
      this._toggle = toggleElement;
      this._menu = findDropdownMenu(toggleElement);
    }

    Dropdown.prototype.show = function () {
      if (!this._menu || !this._toggle) return;
      hideAllDropdowns(this._toggle);
      this._menu.classList.add('show');
      positionDropdownMenu(this._toggle, this._menu);
      var parent = this._menu.closest('.dropdown');
      if (parent) parent.classList.add('show');
      this._toggle.setAttribute('aria-expanded', 'true');
    };

    Dropdown.prototype.hide = function () {
      if (!this._menu || !this._toggle) return;
      this._menu.classList.remove('show');
      this._menu.style.left = '';
      this._menu.style.right = '';
      this._menu.style.top = '';
      this._menu.style.maxWidth = '';
      this._menu.removeAttribute('data-bs-popper');
      var parent = this._menu.closest('.dropdown');
      if (parent) parent.classList.remove('show');
      this._toggle.setAttribute('aria-expanded', 'false');
    };

    Dropdown.prototype.toggle = function () {
      if (!this._menu) return;
      if (this._menu.classList.contains('show')) {
        this.hide();
      } else {
        this.show();
      }
    };

    Dropdown.getInstance = function (element) {
      return dropdownInstances.get(element) || null;
    };

    Dropdown.getOrCreateInstance = function (element) {
      var current = Dropdown.getInstance(element);
      if (current) return current;
      var created = new Dropdown(element);
      dropdownInstances.set(element, created);
      return created;
    };

    function updateCollapseTriggers(targetElement, expanded) {
      if (!targetElement || !targetElement.id) return;
      var selector = '#' + targetElement.id;
      var triggers = document.querySelectorAll('[data-bs-toggle="collapse"]');
      triggers.forEach(function (trigger) {
        var trg = trigger.getAttribute('data-bs-target') || trigger.getAttribute('href');
        if (trg === selector) {
          trigger.setAttribute('aria-expanded', expanded ? 'true' : 'false');
        }
      });
    }

    function Collapse(targetElement) {
      this._target = targetElement;
    }

    Collapse.prototype.show = function () {
      if (!this._target) return;
      this._target.classList.add('show');
      updateCollapseTriggers(this._target, true);
    };

    Collapse.prototype.hide = function () {
      if (!this._target) return;
      this._target.classList.remove('show');
      updateCollapseTriggers(this._target, false);
    };

    Collapse.prototype.toggle = function () {
      if (!this._target) return;
      if (this._target.classList.contains('show')) {
        this.hide();
      } else {
        this.show();
      }
    };

    Collapse.getInstance = function (element) {
      return collapseInstances.get(element) || null;
    };

    Collapse.getOrCreateInstance = function (element) {
      var current = Collapse.getInstance(element);
      if (current) return current;
      var created = new Collapse(element);
      collapseInstances.set(element, created);
      return created;
    };

    window.bootstrap = {
      Modal: Modal,
      Alert: Alert,
      Dropdown: Dropdown,
      Collapse: Collapse
    };

    document.addEventListener('click', function (event) {
      var dropdownToggle = event.target.closest('[data-bs-toggle="dropdown"]');
      if (dropdownToggle) {
        event.preventDefault();
        event.stopPropagation();
        Dropdown.getOrCreateInstance(dropdownToggle).toggle();
        return;
      }

      if (!event.target.closest('.dropdown')) {
        hideAllDropdowns(null);
      }
    });

    document.addEventListener('click', function (event) {
      var collapseToggle = event.target.closest('[data-bs-toggle="collapse"]');
      if (collapseToggle) {
        event.preventDefault();
        var collapseTarget = getTargetFromTrigger(collapseToggle);
        if (collapseTarget) {
          Collapse.getOrCreateInstance(collapseTarget).toggle();
        }
        return;
      }

      var modalToggle = event.target.closest('[data-bs-toggle="modal"]');
      if (modalToggle) {
        event.preventDefault();
        var modalTarget = getTargetFromTrigger(modalToggle);
        if (modalTarget) {
          Modal.getOrCreateInstance(modalTarget).show();
        }
        return;
      }

      var dismissModal = event.target.closest('[data-bs-dismiss="modal"]');
      if (dismissModal) {
        var modalEl = dismissModal.closest('.modal');
        if (modalEl) {
          Modal.getOrCreateInstance(modalEl).hide();
        }
        return;
      }

      var dismissAlert = event.target.closest('[data-bs-dismiss="alert"]');
      if (dismissAlert) {
        var alertEl = dismissAlert.closest('.alert');
        if (alertEl && alertEl.parentNode) {
          alertEl.parentNode.removeChild(alertEl);
        }
      }
    });
  }

  if (typeof window.Chart === 'undefined') {
    window.Chart = function Chart() {
      return {
        destroy: function () {}
      };
    };
  }

  if (typeof window.jQuery === 'undefined' || typeof window.$ === 'undefined') {
    function wrap(elements) {
      var nodes = Array.isArray(elements) ? elements : [];
      var api = {
        elements: nodes,
        length: nodes.length,
        ready: function (callback) {
          if (typeof callback !== 'function') return this;
          if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', callback);
          } else {
            callback();
          }
          return this;
        },
        on: function (eventName, handler) {
          this.elements.forEach(function (el) {
            if (el && el.addEventListener) {
              el.addEventListener(eventName, handler);
            }
          });
          return this;
        },
        addClass: function (className) {
          this.elements.forEach(function (el) {
            if (el && el.classList) el.classList.add(className);
          });
          return this;
        },
        removeClass: function (className) {
          this.elements.forEach(function (el) {
            if (el && el.classList) el.classList.remove(className);
          });
          return this;
        },
        hasClass: function (className) {
          var first = this.elements[0];
          return !!(first && first.classList && first.classList.contains(className));
        },
        data: function (key, value) {
          var first = this.elements[0];
          if (!first || !first.dataset) return value === undefined ? undefined : this;
          if (value === undefined) {
            return first.dataset[key];
          }
          this.elements.forEach(function (el) {
            if (el && el.dataset) el.dataset[key] = value;
          });
          return this;
        },
        html: function (value) {
          if (value === undefined) {
            var first = this.elements[0];
            return first ? first.innerHTML : undefined;
          }
          this.elements.forEach(function (el) {
            if (el) el.innerHTML = value;
          });
          return this;
        },
        text: function (value) {
          if (value === undefined) {
            var first = this.elements[0];
            return first ? first.textContent : undefined;
          }
          this.elements.forEach(function (el) {
            if (el) el.textContent = value;
          });
          return this;
        },
        val: function (value) {
          if (value === undefined) {
            var first = this.elements[0];
            return first ? first.value : undefined;
          }
          this.elements.forEach(function (el) {
            if (el) el.value = value;
          });
          return this;
        },
        append: function () {
          var args = Array.prototype.slice.call(arguments);
          this.elements.forEach(function (parent) {
            if (!parent) return;
            args.forEach(function (item) {
              if (!item) return;
              if (item.elements && item.elements[0]) {
                parent.appendChild(item.elements[0]);
              } else if (item.nodeType) {
                parent.appendChild(item);
              }
            });
          });
          return this;
        },
        prepend: function (item) {
          this.elements.forEach(function (parent) {
            if (!parent || !item) return;
            var node = item.elements && item.elements[0] ? item.elements[0] : item;
            if (node && node.nodeType) {
              parent.insertBefore(node, parent.firstChild);
            }
          });
          return this;
        },
        focus: function () {
          var first = this.elements[0];
          if (first && first.focus) first.focus();
          return this;
        },
        closest: function (selector) {
          var first = this.elements[0];
          if (!first || !first.closest) return wrap([]);
          var match = first.closest(selector);
          return wrap(match ? [match] : []);
        },
        css: function (property, value) {
          this.elements.forEach(function (el) {
            if (!el || !el.style) return;
            if (typeof property === 'string') {
              el.style[property] = value;
            } else if (property && typeof property === 'object') {
              Object.keys(property).forEach(function (key) {
                el.style[key] = property[key];
              });
            }
          });
          return this;
        },
        alert: function (action) {
          if (action === 'close') {
            this.elements.forEach(function (el) {
              if (el && el.parentNode) el.parentNode.removeChild(el);
            });
          }
          return this;
        },
        DataTable: function (options) {
          if (options && typeof options.drawCallback === 'function') {
            options.drawCallback();
          }
          return {
            destroy: function () {},
            draw: function () {}
          };
        }
      };
      return api;
    }

    function $(selector) {
      if (typeof selector === 'function') {
        return wrap([document]).ready(selector);
      }

      if (selector === document) {
        return wrap([document]);
      }

      if (typeof selector === 'string') {
        var trimmed = selector.trim();
        if (trimmed.charAt(0) === '<' && trimmed.charAt(trimmed.length - 1) === '>') {
          var template = document.createElement('template');
          template.innerHTML = trimmed;
          return wrap(template.content.firstElementChild ? [template.content.firstElementChild] : []);
        }
        return wrap(Array.from(document.querySelectorAll(selector)));
      }

      if (selector && selector.nodeType) {
        return wrap([selector]);
      }

      if (selector && typeof selector.length === 'number') {
        return wrap(Array.from(selector));
      }

      return wrap([]);
    }

    $.ajax = function (options) {
      if (!options || !options.url) return;

      var method = (options.method || options.type || 'GET').toUpperCase();
      var headers = options.headers || {};
      var body = options.data;

      if (body && typeof body === 'object' && !(body instanceof FormData)) {
        if (!headers['Content-Type']) {
          headers['Content-Type'] = 'application/json';
        }
        if (headers['Content-Type'].indexOf('application/json') >= 0) {
          body = JSON.stringify(body);
        }
      }

      fetch(options.url, {
        method: method,
        headers: headers,
        body: body
      })
        .then(function (response) {
          return response.text().then(function (raw) {
            var parsed = raw;
            try {
              parsed = JSON.parse(raw);
            } catch (err) {
              parsed = raw;
            }

            if (response.ok) {
              if (typeof options.success === 'function') {
                options.success(parsed);
              }
            } else if (typeof options.error === 'function') {
              options.error({
                status: response.status,
                responseJSON: typeof parsed === 'object' ? parsed : null
              });
            }
          });
        })
        .catch(function (error) {
          if (typeof options.error === 'function') {
            options.error({ message: error.message });
          }
        });
    };

    $.fn = {
      DataTable: function () {
        return {
          destroy: function () {},
          draw: function () {}
        };
      }
    };

    window.$ = $;
    window.jQuery = $;
  }
})(window, document);

