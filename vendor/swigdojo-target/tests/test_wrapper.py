import pytest

from swigdojo_target.wrapper import TargetWrapper


class TestTargetWrapperConstructor:
    def test_constructor_stores_config(self):
        wrapper = TargetWrapper(
            command="python app.py",
            health_port=3000,
            health_path="/ready",
            health_type="tcp",
            proxy=True,
            settle_timeout=120,
        )

        assert wrapper.command == "python app.py"
        assert wrapper.health_port == 3000
        assert wrapper.health_path == "/ready"
        assert wrapper.health_type == "tcp"
        assert wrapper.proxy is True
        assert wrapper.settle_timeout == 120

    def test_constructor_defaults(self):
        wrapper = TargetWrapper(command="python app.py", health_port=3000)

        assert wrapper.health_path == "/health"
        assert wrapper.health_type == "http"
        assert wrapper.proxy is True
        assert wrapper.settle_timeout == 60

    def test_constructor_accepts_command_as_list(self):
        wrapper = TargetWrapper(
            command=["java", "-jar", "app.jar", "--port=9999"],
            health_port=9999,
        )

        assert wrapper.command == "java -jar app.jar --port=9999"


class TestObjectiveDecorator:
    def test_registers_objective_via_decorator(self):
        wrapper = TargetWrapper(command="python app.py", health_port=3000)

        @wrapper.objective(name="check-login", description="Verify login works", public=True)
        def score_login(target_url):
            return True

        assert len(wrapper.objectives) == 1
        obj = wrapper.objectives["check-login"]
        assert obj.name == "check-login"
        assert obj.description == "Verify login works"
        assert obj.public is True
        assert obj.func is score_login

    def test_duplicate_objective_name_fails_fast(self):
        wrapper = TargetWrapper(command="python app.py", health_port=3000)

        @wrapper.objective(name="check-login", description="First", public=True)
        def score_login(target_url):
            return True

        with pytest.raises(ValueError, match="check-login"):

            @wrapper.objective(name="check-login", description="Second", public=False)
            def score_login_again(target_url):
                return True

    def test_invalid_objective_name_fails_fast(self):
        wrapper = TargetWrapper(command="python app.py", health_port=3000)

        with pytest.raises(ValueError):

            @wrapper.objective(name="Check Login", description="Bad name", public=True)
            def score_login(target_url):
                return True

        with pytest.raises(ValueError):

            @wrapper.objective(name="CHECK", description="Uppercase", public=True)
            def score_upper(target_url):
                return True

        with pytest.raises(ValueError):

            @wrapper.objective(name="check@login", description="Special chars", public=True)
            def score_special(target_url):
                return True

    def test_no_objectives_is_valid(self):
        wrapper = TargetWrapper(command="python app.py", health_port=3000)
        assert len(wrapper.objectives) == 0


class TestPassThreshold:
    def test_pass_threshold_stored_on_objective(self):
        wrapper = TargetWrapper(command="python app.py", health_port=3000)

        @wrapper.objective(
            name="check-login", description="Verify login works", public=True, pass_threshold=0.8
        )
        def score_login(ctx):
            return 0.9

        assert wrapper.objectives["check-login"].pass_threshold == 0.8

    def test_pass_threshold_defaults_to_one(self):
        wrapper = TargetWrapper(command="python app.py", health_port=3000)

        @wrapper.objective(name="check-login", description="Verify login works", public=True)
        def score_login(ctx):
            return 1.0

        assert wrapper.objectives["check-login"].pass_threshold == 1.0

    def test_pass_threshold_rejects_below_zero(self):
        wrapper = TargetWrapper(command="python app.py", health_port=3000)

        with pytest.raises(ValueError):

            @wrapper.objective(
                name="check-login", description="Bad", public=True, pass_threshold=-0.1
            )
            def score_login(ctx):
                return 0.5

    def test_pass_threshold_rejects_above_one(self):
        wrapper = TargetWrapper(command="python app.py", health_port=3000)

        with pytest.raises(ValueError):

            @wrapper.objective(
                name="check-login", description="Bad", public=True, pass_threshold=1.1
            )
            def score_login(ctx):
                return 0.5

    def test_pass_threshold_accepts_boundary_values(self):
        wrapper = TargetWrapper(command="python app.py", health_port=3000)

        @wrapper.objective(
            name="obj-zero", description="Zero threshold", public=True, pass_threshold=0.0
        )
        def score_zero(ctx):
            return 0.0

        @wrapper.objective(
            name="obj-one", description="One threshold", public=True, pass_threshold=1.0
        )
        def score_one(ctx):
            return 1.0

        assert wrapper.objectives["obj-zero"].pass_threshold == 0.0
        assert wrapper.objectives["obj-one"].pass_threshold == 1.0


class TestRouteDecorator:
    def test_route_registers_custom_route(self):
        wrapper = TargetWrapper(command="python app.py", health_port=3000)

        @wrapper.route("/telemetry", methods=["POST"])
        async def handle_telemetry(request):
            pass

        assert len(wrapper.routes) == 1
        route = wrapper.routes[0]
        assert route.path == "/telemetry"
        assert route.methods == ["POST"]
        assert route.handler is handle_telemetry

    def test_route_rejects_reserved_path_health(self):
        wrapper = TargetWrapper(command="python app.py", health_port=3000)

        with pytest.raises(ValueError, match="/health"):

            @wrapper.route("/health", methods=["GET"])
            async def handle(request):
                pass

    def test_route_rejects_reserved_path_objectives(self):
        wrapper = TargetWrapper(command="python app.py", health_port=3000)

        with pytest.raises(ValueError, match="/objectives"):

            @wrapper.route("/objectives", methods=["GET"])
            async def handle(request):
                pass

    def test_route_rejects_reserved_path_settle(self):
        wrapper = TargetWrapper(command="python app.py", health_port=3000)

        with pytest.raises(ValueError, match="/settle"):

            @wrapper.route("/settle", methods=["POST"])
            async def handle(request):
                pass

    def test_route_rejects_reserved_path_otel(self):
        wrapper = TargetWrapper(command="python app.py", health_port=3000)

        with pytest.raises(ValueError, match="/otel/v1/traces"):

            @wrapper.route("/otel/v1/traces", methods=["POST"])
            async def handle(request):
                pass

    def test_duplicate_route_path_fails_fast(self):
        wrapper = TargetWrapper(command="python app.py", health_port=3000)

        @wrapper.route("/telemetry", methods=["POST"])
        async def handle_first(request):
            pass

        with pytest.raises(ValueError, match="/telemetry"):

            @wrapper.route("/telemetry", methods=["GET"])
            async def handle_second(request):
                pass


class TestSharedStorage:
    def test_store_and_get_stored(self):
        wrapper = TargetWrapper(command="python app.py", health_port=3000)
        wrapper.store("key1", {"data": 42})
        assert wrapper.get_stored("key1") == {"data": 42}

    def test_get_stored_default_value(self):
        wrapper = TargetWrapper(command="python app.py", health_port=3000)
        assert wrapper.get_stored("missing", default="fallback") == "fallback"

    def test_get_stored_missing_key_returns_none(self):
        wrapper = TargetWrapper(command="python app.py", health_port=3000)
        assert wrapper.get_stored("missing") is None


class TestOtelFlag:
    def test_otel_defaults_to_false(self):
        wrapper = TargetWrapper(command="python app.py", health_port=3000)
        assert wrapper.otel is False

    def test_otel_can_be_enabled(self):
        wrapper = TargetWrapper(command="python app.py", health_port=3000, otel=True)
        assert wrapper.otel is True
